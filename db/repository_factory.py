from db.project_repository import ProjectRepository
from db.investment_repository import InvestmentRepository
from db.depreciation_repository import DepreciationRepository
from db.classification_repository import ClassificationRepository
from db.report_repository import ReportRepository
from db.database_setup_repository import DatabaseSetupRepository
from db.user_repository import UserRepository

class RepositoryFactory:
    """
    Factory class to create repository instances.
    This provides a unified access point for all repositories
    and allows for future dependency injection if needed.
    """
    
    @staticmethod
    def create_project_repository():
        """Create a ProjectRepository instance."""
        return ProjectRepository()
        
    @staticmethod
    def create_investment_repository():
        """Create an InvestmentRepository instance."""
        return InvestmentRepository()
        
    @staticmethod
    def create_depreciation_repository():
        """Create a DepreciationRepository instance."""
        return DepreciationRepository()
        
    @staticmethod
    def create_classification_repository():
        """Create a ClassificationRepository instance."""
        return ClassificationRepository()
        
    @staticmethod
    def create_report_repository():
        """Create a ReportRepository instance."""
        return ReportRepository()
        
    @staticmethod
    def create_database_setup_repository():
        """Create a DatabaseSetupRepository instance."""
        return DatabaseSetupRepository()
        
    @staticmethod
    def create_user_repository():
        """Create a UserRepository instance."""
        return UserRepository()
