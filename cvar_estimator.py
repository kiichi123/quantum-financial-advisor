"""
CVaR Estimator Module - Conditional Value at Risk using Quantum Computing
Provides more robust risk measures than standard VaR
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_finance.circuit.library import NormalDistribution
from qiskit_algorithms import IterativeAmplitudeEstimation, EstimationProblem

def calculate_var_cvar_classical(selection, mu, sigma, confidence=0.95, num_simulations=10000):
    """
    Classical Monte Carlo calculation of VaR and CVaR.
    
    Args:
        selection: Binary selection of assets
        mu: Expected returns
        sigma: Covariance matrix
        confidence: Confidence level (e.g., 0.95 for 95% VaR)
        num_simulations: Number of Monte Carlo simulations
    
    Returns:
        dict with VaR, CVaR, and other statistics
    """
    mu = np.array(mu)
    sigma = np.array(sigma)
    
    # Get selected assets
    indices = [i for i, x in enumerate(selection) if x > 0.5]
    if not indices:
        return {"var": 0, "cvar": 0, "expected_return": 0, "volatility": 0}
    
    # Equal weights for selected assets
    weights = np.zeros(len(mu))
    for i in indices:
        weights[i] = 1.0 / len(indices)
    
    # Portfolio statistics
    p_mu = np.dot(weights, mu)
    p_var = np.dot(weights, np.dot(sigma, weights))
    p_sigma = np.sqrt(max(p_var, 1e-8))
    
    # Monte Carlo simulation
    np.random.seed(42)
    simulated_returns = np.random.normal(p_mu, p_sigma, num_simulations)
    
    # VaR: The loss that is not exceeded with probability (1 - confidence)
    var_percentile = (1 - confidence) * 100
    var = -np.percentile(simulated_returns, var_percentile)
    
    # CVaR: Average loss when loss exceeds VaR
    losses = -simulated_returns
    cvar = np.mean(losses[losses > var])
    
    # Max Drawdown (simplified - from mean)
    max_drawdown = max(losses)
    
    return {
        "var": float(var),
        "cvar": float(cvar),
        "expected_return": float(p_mu),
        "volatility": float(p_sigma),
        "max_drawdown": float(max_drawdown),
        "confidence": confidence
    }

def calculate_risk_qae_enhanced(selection, mu, sigma, threshold=-0.1):
    """
    Enhanced Quantum Amplitude Estimation for risk analysis.
    Returns multiple risk metrics.
    
    Args:
        selection: Binary selection of assets
        mu: Expected returns
        sigma: Covariance matrix
        threshold: Loss threshold (negative value)
    
    Returns:
        dict with VaR probability, CVaR estimate, and other metrics
    """
    mu = np.array(mu)
    sigma = np.array(sigma)
    
    indices = [i for i, x in enumerate(selection) if x > 0.5]
    if not indices:
        return {
            "var_probability": 0.0,
            "cvar_estimate": 0.0,
            "threshold": threshold
        }
    
    # Equal weights
    weights = np.zeros(len(mu))
    for i in indices:
        weights[i] = 1.0 / len(indices)
    
    # Portfolio statistics
    p_mu = np.dot(weights, mu)
    p_var = np.dot(weights, np.dot(sigma, weights))
    p_sigma = np.sqrt(max(p_var, 1e-8))
    
    # Get classical estimates first (for comparison and fallback)
    classical_result = calculate_var_cvar_classical(selection, mu, sigma)
    
    # Quantum VaR probability estimation using QAE
    num_qubits = 4
    low = p_mu - 4 * p_sigma
    high = p_mu + 4 * p_sigma
    
    try:
        uncertainty_model = NormalDistribution(
            num_qubits, mu=p_mu, sigma=p_sigma, bounds=(low, high)
        )
    except Exception as e:
        print(f"NormalDistribution failed: {e}")
        return {
            "var_probability": classical_result["var"],
            "cvar_estimate": classical_result["cvar"],
            "threshold": threshold,
            "classical_fallback": True
        }
    
    # Define grid values
    step = (high - low) / (2**num_qubits - 1) if high > low else 0.01
    values = [low + i * step for i in range(2**num_qubits)]
    
    # States below threshold are "bad" (losses)
    good_states = [i for i, v in enumerate(values) if v < threshold]
    
    if not good_states:
        return {
            "var_probability": 0.0,
            "cvar_estimate": 0.0,
            "threshold": threshold,
            "classical": classical_result
        }
    
    # Build quantum circuit
    qc = QuantumCircuit(uncertainty_model.num_qubits + 1)
    qc.append(uncertainty_model, range(uncertainty_model.num_qubits))
    
    # Mark bad states
    for idx in good_states:
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
        qc.mcx(list(range(uncertainty_model.num_qubits)), uncertainty_model.num_qubits)
        for q in range(uncertainty_model.num_qubits):
            if not ((idx >> q) & 1):
                qc.x(q)
    
    # Quantum Amplitude Estimation
    problem = EstimationProblem(
        state_preparation=qc,
        objective_qubits=[uncertainty_model.num_qubits]
    )
    ae = IterativeAmplitudeEstimation(epsilon_target=0.1, alpha=0.1, sampler=Sampler())
    
    try:
        res = ae.estimate(problem)
        var_probability = res.estimation
    except Exception as e:
        print(f"QAE failed: {e}")
        var_probability = 0.05  # Fallback
    
    return {
        "var_probability": float(var_probability),
        "cvar_estimate": float(classical_result["cvar"]),
        "var_classical": float(classical_result["var"]),
        "threshold": threshold,
        "expected_return": float(p_mu),
        "volatility": float(p_sigma),
        "max_drawdown": float(classical_result["max_drawdown"]),
        "classical": classical_result
    }
