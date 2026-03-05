# logger_config.py
import logging

def setup_shared_logger():
    logger = logging.getLogger("shared_logger")  # 关键：使用固定名称
    logger.setLevel(logging.INFO)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # 添加普通日志文件处理器（指定UTF-8编码）
    file_handler = logging.FileHandler("app.log", encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # 新增错误日志文件处理器（指定UTF-8编码）
    error_handler = logging.FileHandler("errors.log", encoding='utf-8')
    error_handler.setLevel(logging.INFO)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'))
    
    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
    
    return logger