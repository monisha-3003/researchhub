from app import app
from db import db
from models import Publication, Scholar
from datetime import datetime

with app.app_context():
    # Clear existing publications to avoid duplicates for this demo
    Publication.query.delete()
    
    # Dr. Gopi Krishnan's Scholars
    # ID: 1, Name: Lekisha Raj
    # ID: 2, Name: Monisha Devi
    
    pubs = [
        # Lekisha Raj
        Publication(
            scholar_id=1,
            title="Advanced Machine Learning in Distributed Systems",
            journal="IEEE Transactions on Neural Networks",
            pub_type="journal",
            year=2023,
            doi="10.1109/TNNLS.2023.1234567",
            description="Exploration of decentralized learning algorithms.",
            status="published",
            visibility="public"
        ),
        Publication(
            scholar_id=1,
            title="Privacy-Preserving Federated Learning",
            journal="NeurIPS 2024",
            pub_type="conference",
            year=2024,
            doi="10.48550/arXiv.2401.0001",
            description="Multi-party computation for AI safety.",
            status="published",
            visibility="public"
        ),
        Publication(
            scholar_id=1,
            title="Real-time Anomaly Detection in IoT Networks",
            journal="ACM Computing Surveys",
            pub_type="journal",
            year=2025,
            doi="10.1145/1234567.8901234",
            description="Survey on graph neural networks for security.",
            status="under_review",
            visibility="faculty"
        ),
        
        # Monisha Devi
        Publication(
            scholar_id=2,
            title="Quantum Cryptography and Blockchain Security",
            journal="Nature Communications",
            pub_type="journal",
            year=2024,
            doi="10.1038/s41467-024-00001",
            description="Resilience of blockchain protocols against Grover's algorithm.",
            status="published",
            visibility="public"
        ),
        Publication(
            scholar_id=2,
            title="Zero-Knowledge Proofs for Identity Management",
            journal="Eurocrypt 2024",
            pub_type="conference",
            year=2024,
            doi="10.1007/111-222-333",
            description="Efficient zk-SNARKs for mobile devices.",
            status="under_review",
            visibility="faculty"
        )
    ]
    
    db.session.add_all(pubs)
    db.session.commit()
    print(f"Successfully seeded {len(pubs)} publications.")
