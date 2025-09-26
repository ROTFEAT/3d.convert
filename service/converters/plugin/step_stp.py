import sys
from service.converters.base import BaseConverter
import os
import time
import shutil
import traceback

class STEPToSTPConverter(BaseConverter):
    """将STEP文件(.step)转换为STP文件(.stp)的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STEP文件转换为STP文件
        
        参数:
            input_path: STEP文件路径
            output_path: 输出STP文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.stp")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STEP到STP转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
                
            # 由于.step和.stp实际上是同一文件格式的不同扩展名，
            # 我们只需简单复制文件并修改扩展名
            print("[INFO] 复制文件并修改扩展名...")
            shutil.copy2(input_path, output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STP文件创建成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 转换失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STEP到STP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STP成功: {output_path}")
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STEP到STP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "step"
    
    def output_format(self):
        return "stp"


class STPToSTEPConverter(BaseConverter):
    """将STP文件(.stp)转换为STEP文件(.step)的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STP文件转换为STEP文件
        
        参数:
            input_path: STP文件路径
            output_path: 输出STEP文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.step")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STP到STEP转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
                
            # 由于.step和.stp实际上是同一文件格式的不同扩展名，
            # 我们只需简单复制文件并修改扩展名
            print("[INFO] 复制文件并修改扩展名...")
            shutil.copy2(input_path, output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STEP文件创建成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 转换失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STP到STEP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STEP成功: {output_path}")
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STP到STEP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "stp"
    
    def output_format(self):
        return "step"


from utils.file_utils import add_random_prefix
# 测试代码
if __name__ == "__main__":
    # 测试STEP到STP转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.step"
    if os.path.exists(input_file_path):
        # 创建拷贝以避免影响原文件
        copy_path = "C:\\Users\\13016\\Downloads\\good222.step"
        shutil.copyfile(input_file_path, copy_path)
        test_path = add_random_prefix(copy_path)
        
        print(f"[INFO] 测试STEP到STP转换，使用自动输出路径")
        converter = STEPToSTPConverter()
        success, output_path = converter.convert(test_path)
        print(f"[RESULT] STEP到STP转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试STP到STEP转换
            stp_input_path = output_path  # 使用前一步的输出作为输入
            print(f"[INFO] 测试STP到STEP转换，使用自动输出路径")
            converter = STPToSTEPConverter()
            success, output_path = converter.convert(stp_input_path)
            print(f"[RESULT] STP到STEP转换结果: {'成功' if success else '失败'}")
    else:
        print(f"[ERROR] 测试文件不存在: {input_file_path}")
    
    print("=" * 50)
    print("[INFO] 插件转换测试完成")
    print("=" * 50)
