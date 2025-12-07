"""Config API Endpoints - Expose configuration to frontend."""

from fastapi import APIRouter
import logging

from app.models.config_models import FrontendConfig
from app.services.s3_config_loader import (
    get_chatbot_config, get_vector_store_config, reload_configs
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=FrontendConfig)
async def get_frontend_config():
    """
    Get frontend-relevant configuration.
    
    Returns feature flags and settings needed by the UI.
    """
    config = get_chatbot_config()
    return FrontendConfig.from_chatbot_config(config)


@router.post("/reload")
async def reload_configuration():
    """
    Reload configuration from S3.
    
    This allows updating configuration without restarting the server.
    """
    try:
        reload_configs()
        return {
            "message": "Configuration reloaded successfully",
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Failed to reload config: {e}")
        return {
            "message": f"Failed to reload: {str(e)}",
            "status": "error"
        }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers.
    """
    try:
        config = get_chatbot_config()
        return {
            "status": "healthy",
            "app_name": config.app_name,
            "version": config.version
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/features")
async def get_feature_flags():
    """
    Get feature flags only.
    """
    config = get_chatbot_config()
    return {
        "enable_streaming": config.features.enable_streaming,
        "enable_advanced_charts": config.features.enable_advanced_charts,
        "enable_sql_explanation": config.features.enable_sql_explanation,
        "enable_debug_mode": config.features.enable_debug_mode,
        "default_max_rows": config.features.default_max_rows
    }
