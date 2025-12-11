import numpy as np
import pickle
import matplotlib.pyplot as plt

def create_data(num_assets=2, seed=123):
    np.random.seed(seed)
    # Generate random expected returns
    mu = np.random.uniform(0.01, 0.1, num_assets)
    # Generate random covariance matrix
    A = np.random.uniform(-0.1, 0.1, (num_assets, num_assets))
    sigma = np.dot(A, A.T) + np.eye(num_assets) * 0.05
    
    print("Expected returns (mu):")
    print(mu)
    print("\nCovariance matrix (sigma):")
    print(sigma)
    
    return mu, sigma

if __name__ == "__main__":
    mu, sigma = create_data()
    
    # Save to file
    with open('portfolio_data.pkl', 'wb') as f:
        pickle.dump({'mu': mu, 'sigma': sigma}, f)
    
    print("\nData saved to portfolio_data.pkl")
