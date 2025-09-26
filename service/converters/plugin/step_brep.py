import sys
from service.converters.base import BaseConverter
import os
import time
import traceback
# 大概率可以 但是我手上现在没有阅读器可以看brep
#转换回step是ok的
# 使用FreeCAD库进行转换
try:
    import FreeCAD
    import Part
except ImportError:
    print("[ERROR] 无法导入FreeCAD模块。请确保FreeCAD已安装并且环境变量正确设置。")
    sys.exit(1)

class STEPToBREPConverter(BaseConverter):
    """将STEP文件转换为BREP文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STEP文件转换为brep文件
        
        参数:
            input_path: STEP文件路径
            output_path: 输出brep文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - precision: 转换精度 (默认为0.01)
                   - include_metadata: 是否包含元数据 (默认为True)
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径，使用.brep扩展名
            output_path = os.path.join(input_dir, f"{input_basename}.brep")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        # 提取参数
        precision = kwargs.get('precision', 0.01)
        include_metadata = kwargs.get('include_metadata', True)
        
        print(f"[INFO] 开始STEP到BREP转换: {input_path} -> {output_path}")
        print(f"[INFO] 使用参数: precision={precision}, include_metadata={include_metadata}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
                
            # 使用FreeCAD加载STEP文件
            print("[INFO] 正在加载STEP文件...")
            
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
            
            # 转换处理
            # 注意：以下是brep转换的示例代码，实际实现可能需要根据brep格式规范调整
            print("[INFO] 开始处理STEP对象并转换为brep格式...")
            
            # 收集所有形状对象
            shapes = []
            for obj in doc.Objects:
                if hasattr(obj, "Shape"):
                    shapes.append(obj.Shape)
                    print(f"[INFO] 处理形状: {obj.Name}, 面数: {len(obj.Shape.Faces)}")
            
            if not shapes:
                print("[ERROR] 没有找到有效的形状对象")
                return False, None
                
            # brep格式转换逻辑
            # 这里需要根据brep格式的具体规范实现转换逻辑
            print(f"[INFO] 正在转换为brep格式 (精度: {precision})...")
            
            # 使用FreeCAD的brep导出功能
            for i, shape in enumerate(shapes):
                shape_name = f"Shape_{i}"
                shape.exportBrep(output_path)
                print(f"[INFO] 形状已导出为BREP: {shape_name}")
            
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] BREP文件生成成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 输出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STEP到brep转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为brep成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STEP到brep转换失败: {str(e)}")
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
        return "brep"  # 输出格式为brep


class BREPToSTEPConverter(BaseConverter):
    """将BREP文件转换为STEP文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将BREP文件转换为STEP文件
        
        参数:
            input_path: BREP文件路径
            output_path: 输出STEP文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(input_dir, f"{input_basename}.step")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始BREP到STEP转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            
            print("[INFO] 正在解析BREP文件...")
            
            # 创建一个新的FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 直接使用Part模块导入BREP文件
            shape = Part.Shape()
            shape.read(input_path)
            
            print("[INFO] 正在创建形状对象...")
            
            # 创建一个新的对象，并将导入的形状分配给它
            obj_name = "ImportedObject"
            shape_obj = doc.addObject("Part::Feature", obj_name)
            shape_obj.Shape = shape
            
            print(f"[INFO] 解析对象 {obj_name}")
            
            # 导出为STEP文件
            print("[INFO] 正在导出为STEP文件...")
            Part.export([shape_obj], output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STEP文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] BREP到STEP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STEP成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] BREP到STEP转换失败: {str(e)}")
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
        # 已修改为brep
        return "brep"  # 原来是"brep"
    
    def output_format(self):
        return "step"
import shutil
from utils.file_utils import add_random_prefix
# 测试代码
if __name__ == "__main__":
    # 测试STEP到brep转换 - 使用自动生成的输出路径
    input_file_path = "C:\\Users\\13016\\Downloads\\good.step"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.step"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    
    if os.path.exists(input_file_path):
        print(f"[INFO] 测试STEP到BREP转换，使用自动输出路径")
        converter = STEPToBREPConverter()
        success, output_path = converter.convert(input_file_path)
        print(f"[RESULT] St: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试brep到STEP转换 - 使用自动生成的输出路径
            brep_input_path = output_path  # 使用前一步的输出作为输入
            print(f"[INFO] 测试BREP到STEP转换，使用自动输出路径")
            converter = BREPToSTEPConverter()
            success, output_path = converter.convert(brep_input_path)
            print(f"[RESULT]BREP到STEP转换结果: {'成功' if success else '失败'}")
    else:
        print(f"[ERROR] 测试文件不存在: {input_file_path}")
    
    print("=" * 50)
    print("[INFO] 插件转换测试完成")
    print("=" * 50)
