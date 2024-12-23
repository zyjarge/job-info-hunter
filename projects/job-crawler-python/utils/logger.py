import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, level=logging.INFO):
    """
    设置日志记录器
    :param name: 日志名称，用于确定日志文件名，如 'zhipin' 或 'liepin'
    :param level: 日志等级，默认为 INFO
    :return: logger 实例
    """
    # 创建 logs 目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 使用传入的名称创建日志文件路径
    log_file = f'logs/{name}.log'
    
    logger = logging.getLogger(name)
    logger.setLevel(level)  # 使用传入的日志等级
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 文件处理器 - 设置最大10MB，保留3个备份文件
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)  # 使用传入的日志等级
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)  # 使用传入的日志等级
    
    # 清除已存在的处理器
    logger.handlers.clear()
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger