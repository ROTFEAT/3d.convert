import sys
from api.service.converters.base import BaseConverter
import os
import time
import traceback
import shutil
import tempfile

# 添加trimesh库导入
try:
    import trimesh
except ImportError:
    print("[ERROR] 无法导入trimesh模块。请安装: pip install trimesh")
    
# 使用FreeCAD库进行转换
try:
    import FreeCAD
    import Part
    import Mesh
    import MeshPart
except ImportError:
    print("[ERROR] 无法导入FreeCAD模块。请确保FreeCAD已安装并且环境变量正确设置。")
    sys.exit(1)

class STLToSTEPConverter(BaseConverter):
    """将STL文件转换为STEP文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为STEP文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出STEP文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - tolerance: 网格转换的公差 (默认为0.1)
                   - max_faces: 最大面数，超过此值将进行优化 (默认为25000)
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.step")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
 
        # 提取参数
        tolerance = kwargs.get('tolerance', 0.1)
        max_faces = kwargs.get('max_faces', 8000)
        print(f"[INFO] 开始STL到STEP转换: {input_path} -> {output_path}")
        print(f"[INFO] 使用参数: tolerance={tolerance}, max_faces={max_faces}")
        start_time = time.time()
        
        # 临时文件路径，如果需要优化
        optimized_stl_path = None
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
            
            # 检查面数并在必要时优化
            try:
                print("[INFO] 加载STL文件以检查面数...")
                mesh = trimesh.load(input_path)
                faces_count = len(mesh.faces)
                print(f"[INFO] STL文件面数: {faces_count}")
                
                if faces_count > max_faces:
                    print(f"[INFO] 面数超过最大限制({max_faces})，开始优化...")
                    # 创建临时文件
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.stl')
                    temp_file.close()
                    optimized_stl_path = temp_file.name
                    
                    # 计算简化比例
                    ratio = max_faces / faces_count
                    # 简化网格
                    simplified_mesh = mesh.simplify_quadratic_decimation(max_faces)
                    print(f"[INFO] 优化后面数: {len(simplified_mesh.faces)}")
                    
                    # 保存优化后的STL
                    simplified_mesh.export(optimized_stl_path)
                    print(f"[INFO] 优化后的STL已保存到临时文件: {optimized_stl_path}")
                    
                    # 更新输入路径为优化后的文件
                    actual_input_path = optimized_stl_path
                else:
                    print("[INFO] 面数在允许范围内，无需优化")
                    actual_input_path = input_path
            except Exception as e:
                print(f"[WARNING] 检查/优化面数时出错: {str(e)}")
                print("[INFO] 将继续使用原始STL文件进行转换")
                actual_input_path = input_path
                
            # 使用FreeCAD加载STL文件
            print("[INFO] 正在加载STL文件...")
            
            # 创建FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 导入STL网格
            Mesh.insert(actual_input_path, doc.Name)
            print("[INFO] 导入STL文件成功")
            
            # 确保导入成功
            if len(doc.Objects) == 0:
                print("[ERROR] 导入网格失败，没有创建对象")
                return False, None
                
            mesh_obj = doc.Objects[0]
            print(f"[INFO] 获取到导入的网格对象: {mesh_obj.Name}")
            
            # 创建形状对象
            print("[INFO] 创建Part形状对象")
            shape_obj = doc.addObject("Part::Feature", "CADShape")
            
            # 使用正确的方法创建形状
            shape = Part.Shape()
            print(f"[INFO] 正在将网格转换为形状 (tolerance={tolerance})...")
            shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, tolerance, True)
            
            if shape.isNull():
                print("[ERROR] 无法从网格创建有效形状")
                return False, None
            
            # 记录形状信息
            print(f"[INFO] 创建形状成功: 面={len(shape.Faces)}")
            shape_obj.Shape = shape
            
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
            print(f"[INFO] STL到STEP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STEP成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到STEP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
                
            return False, None
        finally:
            # 清理临时文件
            if optimized_stl_path and os.path.exists(optimized_stl_path):
                try:
                    os.remove(optimized_stl_path)
                    print(f"[INFO] 已清理临时优化STL文件")
                except:
                    print(f"[WARNING] 无法清理临时文件: {optimized_stl_path}")
    
    def input_format(self):
        return "stl"
    
    def output_format(self):
        return "step"


class STEPToSTLConverter(BaseConverter):
    """将STEP文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STEP文件转换为STL文件
        
        参数:
            input_path: STEP文件路径
            output_path: 输出STL文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - linear_deflection: 线性偏差 (默认为0.1)
                   - angular_deflection: 角度偏差 (默认为0.5)
                   - ascii: 是否使用ASCII格式STL (默认为False)
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.stl")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        # 提取参数
        linear_deflection = kwargs.get('linear_deflection', 0.1)
        angular_deflection = kwargs.get('angular_deflection', 0.5)
        ascii_format = kwargs.get('ascii', False)
        
        print(f"[INFO] 开始STEP到STL转换: {input_path} -> {output_path}")
        print(f"[INFO] 使用参数: linear_deflection={linear_deflection}, angular_deflection={angular_deflection}, ascii={ascii_format}")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
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
            
            # 创建网格对象
            mesh_objects = []
            
            for i, obj in enumerate(doc.Objects):
                if hasattr(obj, "Shape"):
                    try:
                        # 创建网格对象
                        mesh_name = f"{obj.Name}_mesh"
                        mesh_obj = doc.addObject("Mesh::Feature", mesh_name)
                        
                        # 创建网格数据
                        mesh_data = Mesh.Mesh()
                        # 将形状转换为网格，使用提供的参数
                        mesh_data.addFacets(obj.Shape.tessellate(linear_deflection))
                        
                        # 将网格数据分配给网格对象
                        mesh_obj.Mesh = mesh_data
                        
                        mesh_objects.append(mesh_obj)
                        print(f"[INFO] 为对象 {obj.Name} 创建了网格")
                    except Exception as e:
                        print(f"[WARNING] 为对象 {obj.Name} 创建网格时出错: {e}")
            
            if not mesh_objects:
                print("[ERROR] 没有成功创建任何网格对象")
                return False, None
            
            # 导出为STL文件
            print(f"[INFO] 正在导出为STL文件 (格式: {'ASCII' if ascii_format else '二进制'})...")
            
            # 导出STL
            if ascii_format:
                Mesh.export(mesh_objects, output_path, "STL ASC")
            else:
                Mesh.export(mesh_objects, output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STEP到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STEP到STL转换失败: {str(e)}")
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
        return "stl"

# 测试代码
from api.utils.file_utils import add_random_prefix
if __name__ == "__main__":
    # 测试STL到STEP转换 - 使用自动生成的输出路径
    input_file_path = "C:\\Users\\13016\\Downloads\\VjoF_good2224444.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\VjoF_goodsdasd2224444.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    print(f"[INFO] 测试STL到STEP转换，使用自动输出路径")
    converter = STLToSTEPConverter()
    success, output_path = converter.convert(input_file_path)
    print(f"[RESULT] STL到STEP转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试STEP到STL转换 - 使用自动生成的输出路径
        step_input_path = output_path  # 使用前一步的输出作为输入
        print(f"[INFO] 测试STEP到STL转换，使用自动输出路径")
        converter = STEPToSTLConverter()
        success, output_path = converter.convert(step_input_path)
        print(f"[RESULT] STEP到STL转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 插件转换测试完成")
    print("=" * 50)
