import numpy as np
from qiskit_finance.data_providers import RandomDataProvider
from qiskit_finance.applications.optimization import PortfolioOptimization
from qiskit_algorithms import QAOA, SamplingVQE
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_finance.circuit.library import NormalDistribution
from qiskit_algorithms import IterativeAmplitudeEstimation, EstimationProblem
from qiskit import QuantumCircuit

# Mock Market Data Analysis
def analyze_market(text_input):
    """
    Analyzes text input to determine market regime and select candidates.
    Returns:
        tickers (list): List of asset names.
        mu (np.array): Expected returns.
        sigma (np.array): Covariance matrix.
    """
    input_lower = text_input.lower()
    
    # Default: Balanced
    regime = "neutral"
    
    if "inflation" in input_lower or "conflict" in input_lower:
        regime = "defensive"
    elif "growth" in input_lower or "tech" in input_lower or "boom" in input_lower:
        regime = "aggressive"
        
    print(f"Market Regime Detected: {regime}")
    
    # Generate Synthetic Data based on regime
    num_assets = 4
    if regime == "defensive":
        tickers = ["Gold", "Utility", "Bonds", "Consumer Staples"]
        mu = np.array([0.05, 0.04, 0.03, 0.04]) # Stable lower returns
        sigma = np.array([
            [0.02, 0.005, 0.001, 0.01],
            [0.005, 0.02, 0.005, 0.01],
            [0.001, 0.005, 0.01, 0.001],
            [0.01, 0.01, 0.001, 0.02]
        ])
    elif regime == "aggressive":
        tickers = ["Tech", "Crypto", "BioTech", "Semiconductor"]
        mu = np.array([0.15, 0.20, 0.12, 0.18]) # High returns
        # Higher Volatility
        sigma = np.eye(4) * 0.08 + 0.02 
    else:
        tickers = ["S&P500", "Bonds", "RealEstate", "Commodities"]
        mu = np.array([0.08, 0.03, 0.06, 0.05])
        sigma = np.eye(4) * 0.04 + 0.01
        
    return tickers, mu, sigma

def run_quantum_portfolio_optimization(mu, sigma, risk_factor=0.5, budget=2):
    """
    Uses QAOA/VQE to find optimal portfolio selection.
    Maximize: mu.T * x - q * x.T * sigma * x
    Subject to: sum(x) = budget (number of assets to pick)
    """
    
    # Define Portfolio Optimization Problem
    portfolio = PortfolioOptimization(
        expected_returns=mu,
        covariances=sigma,
        risk_factor=risk_factor,
        budget=budget
    )
    
    qp = portfolio.to_quadratic_program()
    
    # Solve using QAOA (Simulated)
    # Using COBYLA optimizer
    optimizer = COBYLA(maxiter=50)
    
    # Using SamplingVQE as QAOA is a type of VQE
    # Or just use QAOA class directly
    qaoa = QAOA(sampler=Sampler(), optimizer=optimizer, reps=1)
    
    # We need a converter to Qiskit Optimization Algorithms
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    
    meo = MinimumEigenOptimizer(qaoa)
    result = meo.solve(qp)
    
    selection = []
    if result.x is not None:
        selection = result.x
        
    return selection, result.fval

def calculate_risk_qae(selection, mu, sigma, threshold=-0.1):
    """
    Calculates risk using QAE for the SELECTED portfolio.
    (Simplified from 02_quantum_optimize.py)
    """
    # Filter stats for selected assets
    # selection is boolean array (0 or 1)
    indices = [i for i, x in enumerate(selection) if x > 0.5]
    
    if not indices:
        return 0.0
    
    # Create sub-portfolio
    # If equal weight among selected
    weights = np.zeros(len(mu))
    for i in indices:
        weights[i] = 1.0 / len(indices)
        
    # Portfolio Mean/Var
    p_mu = np.dot(weights, mu)
    p_var = np.dot(weights, np.dot(sigma, weights))
    p_sigma = np.sqrt(p_var)
    
    # Low Precision QAE for Speed
    num_qubits = 4
    low = p_mu - 3 * p_sigma
    high = p_mu + 3 * p_sigma
    bounds = (low, high)
    
    uncertainty_model = NormalDistribution(num_qubits, mu=p_mu, sigma=p_sigma, bounds=bounds)
    
    # Value Calculation
    def get_values():
        vals = []
        step = (high - low) / (2**num_qubits - 1)
        for i in range(2**num_qubits):
            vals.append(low + i * step)
        return vals
    
    values = get_values()
    good_states = [i for i, v in enumerate(values) if v < threshold]
    
    if not good_states:
        return 0.0
        
    qc = QuantumCircuit(uncertainty_model.num_qubits + 1)
    qc.append(uncertainty_model, range(uncertainty_model.num_qubits))
    
    for idx in good_states:
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
        qc.mcx(list(range(uncertainty_model.num_qubits)), uncertainty_model.num_qubits)
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
                
    problem = EstimationProblem(state_preparation=qc, objective_qubits=[uncertainty_model.num_qubits])
    ae = IterativeAmplitudeEstimation(epsilon_target=0.1, alpha=0.1, sampler=Sampler()) # Very loose for speed
    
    res = ae.estimate(problem)
    return res.estimation        
