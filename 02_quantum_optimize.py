import numpy as np
import pickle
import time
from scipy.stats import norm

# Qiskit imports
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_algorithms import IterativeAmplitudeEstimation, EstimationProblem
# Use 1D Normal Distribution
from qiskit_finance.circuit.library import NormalDistribution

def load_data():
    with open('portfolio_data.pkl', 'rb') as f:
        data = pickle.load(f)
    return data['mu'], data['sigma']

def classical_monte_carlo(mu, sigma, num_samples=10000, weights=None):
    if weights is None:
        weights = np.ones(len(mu)) / len(mu)
    
    # R ~ N(mu, sigma)
    # Portfolio Return Rp = w . R
    R = np.random.multivariate_normal(mu, sigma, num_samples)
    portfolio_returns = np.dot(R, weights)
    
    # Calculate VaR (5%)
    var_95 = np.percentile(portfolio_returns, 5)
    
    return var_95, portfolio_returns

def quantum_var_estimation(mu_p, sigma_p, threshold):
    # Model the Portfolio Return Rp as a single Gaussian N(mu_p, sigma_p^2)
    
    num_qubits = 5  # Adjusted for stability
    
    # Define bounds: +/- 4 std (better coverage for normalization)
    low = mu_p - 4 * sigma_p
    high = mu_p + 4 * sigma_p
    bounds = (low, high)
    
    # 1. Uncertainty Model
    uncertainty_model = NormalDistribution(num_qubits, mu=mu_p, sigma=sigma_p, bounds=bounds)
    
    # 2. Objective: Mark states where Value < Threshold
    values = uncert_model_values(uncertainty_model.num_qubits, bounds)
    good_states_indices = [i for i, v in enumerate(values) if v < threshold]
    
    # DEBUG: Calculate Discretized Probability
    # NormalDistribution coeffs square to probabilities.
    # We can get the probabilities approximately by PDF * step
    # Or just trusting QAE matches this.
    # Let's verify by just printing the number of good states and range
    print(f"Num Qubits: {num_qubits}")
    print(f"Total States: {2**num_qubits}")
    print(f"Num Good States (Value < {threshold:.4f}): {len(good_states_indices)}")
    if len(good_states_indices) > 0:
        print(f"Max Good Value: {values[good_states_indices[-1]]:.4f}")
    
    # Create Oracle
    qc = QuantumCircuit(uncertainty_model.num_qubits + 1)
    qc.append(uncertainty_model, range(uncertainty_model.num_qubits))
    
    # Flip oracle qubit (last one) if state is in good_states_indices
    for idx in good_states_indices:
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
        
        qc.mcx(list(range(uncertainty_model.num_qubits)), uncertainty_model.num_qubits)
        
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
                
    prob_problem = EstimationProblem(
        state_preparation=qc,
        objective_qubits=[uncertainty_model.num_qubits]
    )
    
    # Run QAE
    ae = IterativeAmplitudeEstimation(
        epsilon_target=0.01,
        alpha=0.05,
        sampler=Sampler()
    )
    
    result = ae.estimate(prob_problem)
    return result.estimation

def uncert_model_values(num_qubits, bounds):
    low, high = bounds
    values = []
    # Qiskit NormalDistribution mapping:
    # 0 -> low, 2^n-1 -> high
    # x_i = low + i * (high - low) / (2^n - 1)
    step = (high - low) / (2**num_qubits - 1)
    for i in range(2**num_qubits):
        values.append(low + i * step)
    return values

if __name__ == "__main__":
    t0 = time.time()
    mu, sigma = load_data()
    
    # Define Weights
    weights = np.ones(len(mu)) / len(mu)
    
    # Calculate Portfolio parameters roughly
    # Rp ~ N(w.mu, w.Sigma.w)
    p_mu = np.dot(weights, mu)
    p_var = np.dot(weights, np.dot(sigma, weights))
    p_sigma = np.sqrt(p_var)
    
    print(f"Portfolio Mean: {p_mu:.4f}")
    print(f"Portfolio Volatility: {p_sigma:.4f}")
    
    # 1. Classical Baseline
    print("\n--- Classical Monte Carlo ---")
    st = time.time()
    var_95, returns = classical_monte_carlo(mu, sigma, num_samples=10000, weights=weights)
    print(f"Estimated VaR (5% quantile): {var_95:.4f}")
    
    # Calculate exact prob for check
    exact_prob = norm.cdf(var_95, loc=p_mu, scale=p_sigma)
    print(f"Theoretical Prob: {exact_prob:.4f}")
    print(f"Time: {time.time() - st:.4f}s")
    
    # 2. Quantum Estimation
    print("\n--- Quantum Amplitude Estimation ---")
    print(f"Target Threshold: {var_95:.4f}")
    st = time.time()
    
    try:
        prob = quantum_var_estimation(p_mu, p_sigma, var_95)
        print(f"Estimated Probability: {prob:.4f}")
    except Exception as e:
        print(f"Quantum execution failed: {e}")
        import traceback
        traceback.print_exc()

    print(f"Time: {time.time() - st:.4f}s")
    print(f"\nTotal Run Time: {time.time() - t0:.4f}s")
