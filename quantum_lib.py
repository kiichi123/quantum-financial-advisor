"""
Quantum Library - Core quantum computing logic for portfolio optimization
Integrates with LLM and real stock data
"""
import numpy as np
from qiskit_finance.applications.optimization import PortfolioOptimization
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_finance.circuit.library import NormalDistribution
from qiskit_algorithms import IterativeAmplitudeEstimation, EstimationProblem
from qiskit import QuantumCircuit
from qiskit_optimization.algorithms import MinimumEigenOptimizer

# Import our modules
from llm_analyzer import analyze_with_llm
from stock_data import get_stock_data

def analyze_market(user_input: str) -> dict:
    """
    Analyze market conditions using LLM and fetch real stock data.
    
    Returns:
        dict with tickers, names, mu, sigma, reasoning
    """
    # Step 1: LLM Analysis
    llm_result = analyze_with_llm(user_input)
    
    # Step 2: Get real stock data for recommended tickers
    tickers = llm_result.get("tickers", ["SPY", "QQQ", "DIA", "IWM"])
    stock_result = get_stock_data(tuple(tickers))
    
    return {
        "regime": llm_result.get("regime", "neutral"),
        "sectors": llm_result.get("sectors", []),
        "reasoning": llm_result.get("reasoning", ""),
        "tickers": stock_result["tickers"],
        "names": stock_result.get("names", stock_result["tickers"]),
        "mu": stock_result["mu"],
        "sigma": stock_result["sigma"],
        "last_prices": stock_result.get("last_prices", []),
        "returns_1y": stock_result.get("returns_1y", []),
        "synthetic": stock_result.get("synthetic", False)
    }

def run_quantum_portfolio_optimization(mu, sigma, risk_factor=0.5, budget=2):
    """
    Uses QAOA/VQE to find optimal portfolio selection.
    """
    mu = np.array(mu)
    sigma = np.array(sigma)
    
    portfolio = PortfolioOptimization(
        expected_returns=mu,
        covariances=sigma,
        risk_factor=risk_factor,
        budget=budget
    )
    
    qp = portfolio.to_quadratic_program()
    
    optimizer = COBYLA(maxiter=50)
    qaoa = QAOA(sampler=Sampler(), optimizer=optimizer, reps=1)
    
    meo = MinimumEigenOptimizer(qaoa)
    result = meo.solve(qp)
    
    selection = []
    if result.x is not None:
        selection = result.x
        
    return selection, result.fval

def calculate_risk_qae(selection, mu, sigma, threshold=-0.1):
    """
    Calculates risk using Quantum Amplitude Estimation.
    """
    mu = np.array(mu)
    sigma = np.array(sigma)
    
    indices = [i for i, x in enumerate(selection) if x > 0.5]
    
    if not indices:
        return 0.0
    
    weights = np.zeros(len(mu))
    for i in indices:
        weights[i] = 1.0 / len(indices)
        
    p_mu = np.dot(weights, mu)
    p_var = np.dot(weights, np.dot(sigma, weights))
    p_sigma = np.sqrt(max(p_var, 1e-8))
    
    num_qubits = 4
    low = p_mu - 3 * p_sigma
    high = p_mu + 3 * p_sigma
    bounds = (low, high)
    
    try:
        uncertainty_model = NormalDistribution(num_qubits, mu=p_mu, sigma=p_sigma, bounds=bounds)
    except Exception as e:
        print(f"NormalDistribution failed: {e}")
        return 0.05  # Fallback
    
    def get_values():
        vals = []
        step = (high - low) / (2**num_qubits - 1) if high > low else 0.01
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
    ae = IterativeAmplitudeEstimation(epsilon_target=0.1, alpha=0.1, sampler=Sampler())
    
    try:
        res = ae.estimate(problem)
        return res.estimation
    except Exception as e:
        print(f"QAE failed: {e}")
        return 0.05
