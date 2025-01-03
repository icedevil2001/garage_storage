from loguru import logger
import os

def setup_logger(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configure loguru to write to file with rotation
    logger.add(
        'logs/garage_storage.log',
        rotation='10 MB',  # Rotate when file reaches 10MB
        retention=10,      # Keep 10 rotated files
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {file}:{line}",
        level="DEBUG"
    )
    
    logger.info('Garage Storage startup')
    return logger
