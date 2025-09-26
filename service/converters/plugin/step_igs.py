import sys
from service.converters.base import BaseConverter
import os
import time
import shutil
import traceback

class STEPToIGSConverter(BaseConverter):
    """将STEP文件(.step)转换为IGS文件(.igs)的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STEP文件转换为IGS文件
        
        参数:
            input_path: STEP文件路径
            output_path: 输出IGS文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.igs")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STEP到IGS转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
                
            # 使用FreeCAD进行实际转换
            print("[INFO] 使用FreeCAD进行STEP到IGS转换...")
            
            # 导入FreeCAD模块
            try:
                import FreeCAD
                import Part
            except ImportError:
                print("[ERROR] 无法导入FreeCAD模块。请确保FreeCAD已安装并且环境变量正确设置。")
                return False, None
            
            # 创建FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 导入STEP文件
            Part.insert(input_path, doc.Name)
            print("[INFO] 导入STEP文件成功")
            
            # 确保导入成功
            if len(doc.Objects) == 0:
                print("[ERROR] 导入CAD文件后没有对象")
                return False, None
            
            print(f"[INFO] 成功导入 {len(doc.Objects)} 个对象")
            
            # 收集所有形状对象
            shapes = []
            for obj in doc.Objects:
                if hasattr(obj, "Shape"):
                    shapes.append(obj)
                    print(f"[INFO] 处理形状: {obj.Name}, 面数: {len(obj.Shape.Faces)}")
            
            if not shapes:
                print("[ERROR] 没有找到有效的形状对象")
                return False, None
            
            # 导出IGS
            print("[INFO] 正在导出为IGS文件...")
            Part.export(shapes, output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] IGS文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STEP到IGS转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为IGS成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STEP到IGS转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
                
            return False, None
    
    def input_format(self):
        return "step"
    
    def output_format(self):
        return "igs"


class IGSToSTEPConverter(BaseConverter):
    """将IGS文件(.igs)转换为STEP文件(.step)的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将IGS文件转换为STEP文件
        
        参数:
            input_path: IGS文件路径
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
        
        print(f"[INFO] 开始IGS到STEP转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            
            # 使用FreeCAD进行实际转换
            print("[INFO] 使用FreeCAD进行IGS到STEP转换...")
            
            # 导入FreeCAD模块
            try:
                import FreeCAD
                import Part
            except ImportError:
                print("[ERROR] 无法导入FreeCAD模块。请确保FreeCAD已安装并且环境变量正确设置。")
                return False, None
            
            # 创建FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 导入IGS文件
            print("[INFO] 正在加载IGS文件...")
            Part.insert(input_path, doc.Name)
            print("[INFO] 导入IGS文件成功")
            
            # 确保导入成功
            if len(doc.Objects) == 0:
                print("[ERROR] 导入CAD文件后没有对象")
                return False, None
            
            print(f"[INFO] 成功导入 {len(doc.Objects)} 个对象")
            
            # 收集所有形状对象
            shapes = []
            for obj in doc.Objects:
                if hasattr(obj, "Shape"):
                    shapes.append(obj)
                    print(f"[INFO] 处理形状: {obj.Name}, 面数: {len(obj.Shape.Faces)}")
            
            if not shapes:
                print("[ERROR] 没有找到有效的形状对象")
                return False, None
            
            # 导出STEP
            print("[INFO] 正在导出为STEP文件...")
            Part.export(shapes, output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STEP文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] IGS到STEP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STEP成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] IGS到STEP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
                
            return False, None
    
    def input_format(self):
        return "igs"
    
    def output_format(self):
        return "step"


from utils.file_utils import add_random_prefix
# 测试代码
if __name__ == "__main__":
    # 测试STEP到IGS转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.step"
    if os.path.exists(input_file_path):
        # 创建拷贝以避免影响原文件
        copy_path = "C:\\Users\\13016\\Downloads\\good222.step"
        shutil.copyfile(input_file_path, copy_path)
        test_path = add_random_prefix(copy_path)
        
        print(f"[INFO] 测试STEP到IGS转换，使用自动输出路径")
        converter = STEPToIGSConverter()
        success, output_path = converter.convert(test_path)
        print(f"[RESULT] STEP到IGS转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试IGS到STEP转换
            igs_input_path = output_path  # 使用前一步的输出作为输入
            print(f"[INFO] 测试IGS到STEP转换，使用自动输出路径")
            converter = IGSToSTEPConverter()
            success, output_path = converter.convert(igs_input_path)
            print(f"[RESULT] IGS到STEP转换结果: {'成功' if success else '失败'}")
    else:
        print(f"[ERROR] 测试文件不存在: {input_file_path}")
    
    print("=" * 50)
    print("[INFO] 插件转换测试完成")
    print("=" * 50)
