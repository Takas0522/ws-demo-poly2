from setuptools import setup, find_packages

setup(
    name="user-management-service",
    version="1.0.0",
    description="User Management Service with CRUD operations and tenant isolation",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "azure-cosmos>=4.5.1",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
        "email-validator>=2.1.0",
    ],
)
