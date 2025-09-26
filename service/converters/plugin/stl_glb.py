import sys
from service.converters.base import BaseConverter
import trimesh
import os
import time

class STLToGLBConverter(BaseConverter):
    """将STL文件转换为GLB文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为GLB文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出GLB文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.glb")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到GLB转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载STL文件
            print("[INFO] 正在加载STL文件...")
            mesh = trimesh.load(input_path)
            
            if not isinstance(mesh, trimesh.Trimesh):
                print("[ERROR] 无法加载有效的STL网格")
                return False, None
                
            # 记录网格信息
            print(f"[INFO] 成功加载STL网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 导出为GLB文件
            print("[INFO] 正在导出为GLB文件...")
            
            # 导出为GLB格式
            mesh.export(output_path, file_type='glb')
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] GLB文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STL到GLB转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为GLB成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到GLB转换失败: {str(e)}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "stl"
    
    def output_format(self):
        return "glb"


class GLBToSTLConverter(BaseConverter):
    """将GLB文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将GLB文件转换为STL文件
        
        参数:
            input_path: GLB文件路径
            output_path: 输出STL文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - ascii: 布尔值，是否使用ASCII格式STL (默认为False，使用二进制格式)
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
        ascii_format = kwargs.get('ascii', False)
            
        print(f"[INFO] 开始GLB到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载GLB文件
            print(f"[INFO] 正在加载GLB文件...")
            # 导入文件通常返回一个场景
            scene = trimesh.load(input_path)
            
            # 处理场景中的所有网格
            if isinstance(scene, trimesh.Scene):
                print(f"[INFO] 检测到GLB文件包含场景，提取所有网格...")
                # 提取所有网格并合并
                meshes = []
                for geometry_name, geometry in scene.geometry.items():
                    print(f"[INFO] 提取网格: {geometry_name}")
                    if isinstance(geometry, trimesh.Trimesh):
                        # 将网格转换到场景坐标系
                        transform = scene.graph.get(geometry_name)[0]
                        geometry = geometry.copy()
                        geometry.apply_transform(transform)
                        meshes.append(geometry)
                
                if len(meshes) == 1:
                    mesh = meshes[0]
                elif len(meshes) > 1:
                    print(f"[INFO] 合并 {len(meshes)} 个网格...")
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    print(f"[WARNING] 未在GLB文件中找到有效网格")
                    return False, None
            elif isinstance(scene, trimesh.Trimesh):
                # 直接是单个网格
                mesh = scene
            else:
                print(f"[ERROR] 无法处理的GLB文件格式")
                return False, None
            
            # 记录网格信息
            print(f"[INFO] 成功加载GLB网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 导出为STL文件
            print(f"[INFO] 正在导出为STL文件 (格式: {'ASCII' if ascii_format else '二进制'})...")
            
            # 导出STL
            if ascii_format:
                try:
                    mesh.export(output_path, file_type='stl_ascii')
                except:
                    mesh.export(output_path, file_type='stl', binary=False)
            else:
                mesh.export(output_path, file_type='stl')
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] GLB到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] GLB到STL转换失败: {str(e)}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "glb"
    
    def output_format(self):
        return "stl"


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与GLB转换测试")
    print("=" * 50)
    
    # 测试STL到GLB转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    
    if os.path.exists(input_file_path):
        print(f"[INFO] 测试STL到GLB转换，使用自动输出路径")
        
        converter = STLToGLBConverter()
        success, output_path = converter.convert(input_file_path)
        print(f"[RESULT] STL到GLB转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试GLB到STL转换
            glb_path = output_path
            print(f"[INFO] 测试GLB到STL转换，使用自动输出路径")
            
            converter = GLBToSTLConverter()
            success, stl_path = converter.convert(glb_path)
            print(f"[RESULT] GLB到STL转换结果: {'成功' if success else '失败'}")
    else:
        print(f"[ERROR] 测试文件不存在: {input_file_path}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
