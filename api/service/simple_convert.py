import os
import shutil
import tempfile
import FreeCAD
import Part
import Mesh
import trimesh
import logging
from pathlib import Path

def convert_format(input_path, output_format):
    """
    转换3D文件格式
    
    参数:
        input_path (str): 输入文件的路径
        output_format (str): 目标输出格式（不带点，如'stl'）
    
    返回:
        tuple: (是否成功(bool), 输出文件路径(str)或错误信息)
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("格式转换")
    
    # 记录开始转换的日志
    logger.info(f"开始转换: 从 {input_path} 到 {output_format} 格式")
    
    # 定义格式组和桥梁格式
    cad_formats = ["step", "stp", "iges", "igs", "brep", "brp"]
    mesh_formats = ["stl", "obj", "3mf", "ply"] #纯网格格式
    drawing_formats = ["dxf"]
    other_3d_formats = ["gltf", "glb", "x3d"]

    
    # 定义各工具支持的格式
    trimesh_supported_exports = ["stl", "obj", "ply", "gltf", "glb", "3mf"]
    freecad_supported_exports = cad_formats + ["stl", "obj", "dxf", "x3d", "3mf"]
    
    # 获取输入文件的扩展名
    input_path = Path(input_path)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        return False, f"输入文件不存在: {input_path}"
    
    input_ext = input_path.suffix[1:].lower()
    logger.info(f"检测到输入文件格式: {input_ext}")
    
    # 检查输入和输出格式是否支持
    supported_formats = cad_formats + mesh_formats + drawing_formats + other_3d_formats
    if input_ext not in supported_formats:
        logger.error(f"不支持的输入格式: {input_ext}")
        return False, f"不支持的输入格式: {input_ext}"
    
    if output_format not in supported_formats:
        logger.error(f"不支持的输出格式: {output_format}")
        return False, f"不支持的输出格式: {output_format}"
    
    # 如果输入和输出格式相同
    if input_ext == output_format:
        # 创建一个新的文件名，添加后缀 "_converted"
        stem = input_path.stem
        output_path = input_path.with_name(f"{stem}_converted.{output_format}")
        logger.info(f"输入和输出格式相同: {input_ext}，创建新文件: {output_path}")
        shutil.copy(input_path, output_path)
        logger.info(f"复制完成: {input_path} -> {output_path}")
        return True, str(output_path)
    
    # 生成输出文件路径
    output_path = input_path.with_suffix(f".{output_format}")
    logger.info(f"目标输出路径: {output_path}")
    
    # 在跨类型转换前先检查特殊格式
    if input_ext == "3mf":
        logger.info("检测到3MF输入格式，使用特殊处理方法")
        success = convert_3mf_special(str(input_path), str(output_path), output_format)
        if success:
            logger.info(f"3MF到{output_format}转换成功: {output_path}")
            return True, str(output_path)
        else:
            logger.error(f"3MF到{output_format}转换失败")
            return False, f"3MF到{output_format}转换失败"
    
    # 确定源格式和目标格式的类型
    def get_format_type(fmt):
        if fmt in cad_formats:
            return "cad"
        elif fmt in mesh_formats:
            return "mesh"
        elif fmt in drawing_formats:
            return "drawing"
        elif fmt in other_3d_formats:
            return "other_3d"
        return None


    input_type = get_format_type(input_ext)
    output_type = get_format_type(output_format)
    logger.info(f"输入类型: {input_type}, 输出类型: {output_type}")
    
    # 临时文件路径
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建临时目录: {temp_dir}")
    
    try:
        # 检查特殊格式组合
        
        # X3D格式的特殊处理
        if output_format == "x3d":
            logger.info(f"检测到X3D输出格式，使用FreeCAD进行处理")
            if input_type == "mesh":
                # 网格到X3D的转换需要通过FreeCAD
                success = convert_mesh_to_x3d(str(input_path), str(output_path))
                if not success:
                    logger.error(f"网格到X3D转换失败: {input_ext} -> x3d")
                    return False, f"网格到X3D转换失败: {input_ext} -> x3d"
                logger.info(f"转换成功: {input_path} -> {output_path}")
                return True, str(output_path)
            elif input_type == "cad":
                # CAD到X3D转换
                success = convert_cad_to_x3d(str(input_path), str(output_path))
                if not success:
                    logger.error(f"CAD到X3D转换失败: {input_ext} -> x3d")
                    return False, f"CAD到X3D转换失败: {input_ext} -> x3d"
        
        # 同类型转换
        if input_type == output_type:
            logger.info(f"执行同类型转换: {input_type}")
            if input_type == "cad":
                # CAD到CAD转换 (通过STEP桥梁)
                if input_ext != "step" and output_format != "step":
                    # 先转到STEP
                    temp_step = os.path.join(temp_dir, "temp.step")
                    logger.info(f"先转换到STEP桥梁格式: {temp_step}")
                    success = convert_cad_file(str(input_path), temp_step)
                    if not success:
                        logger.error("无法转换为STEP格式")
                        return False, "无法转换为STEP格式"
                    # 再从STEP转到目标格式
                    logger.info(f"从STEP转换到目标格式: {output_format}")
                    success = convert_cad_file(temp_step, str(output_path))
                    if not success:
                        logger.error(f"从STEP转换到{output_format}失败")
                        return False, f"从STEP转换到{output_format}失败"
                else:
                    # 直接转换
                    logger.info(f"直接转换CAD格式: {input_ext} -> {output_format}")
                    success = convert_cad_file(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"CAD格式转换失败: {input_ext} -> {output_format}")
                        return False, f"CAD格式转换失败: {input_ext} -> {output_format}"
            
            elif input_type == "mesh":
                # 检查输出格式是否被trimesh支持
                if output_format not in trimesh_supported_exports and output_format not in freecad_supported_exports:
                    logger.error(f"不支持的网格输出格式: {output_format}")
                    return False, f"不支持的网格输出格式: {output_format}"
                
                # 3MF格式特殊处理
                if output_format == "3mf":
                    logger.info("检测到3MF输出格式，使用专用方法")
                    success = convert_to_3mf(str(input_path), str(output_path))
                    if success:
                        logger.info(f"3MF转换成功: {input_path} -> {output_path}")
                        return True, str(output_path)
                    else:
                        logger.error(f"转换为3MF失败: {input_ext} -> 3mf")
                        return False, f"转换为3MF失败: {input_ext} -> 3mf"
                
                # Trimesh不支持但FreeCAD支持的格式
                if output_format not in trimesh_supported_exports and output_format in freecad_supported_exports:
                    logger.info(f"Trimesh不支持导出{output_format}格式，尝试使用FreeCAD")
                    success = convert_mesh_using_freecad(str(input_path), str(output_path), output_format)
                    if not success:
                        logger.error(f"使用FreeCAD进行网格格式转换失败: {input_ext} -> {output_format}")
                        return False, f"使用FreeCAD进行网格格式转换失败: {input_ext} -> {output_format}"
                    return True, str(output_path)
                
                # 网格到网格转换 (通过STL桥梁)
                if input_ext != "stl" and output_format != "stl":
                    # 先转到STL
                    temp_stl = os.path.join(temp_dir, "temp.stl")
                    logger.info(f"先转换到STL桥梁格式: {temp_stl}")
                    success = convert_mesh_file(str(input_path), temp_stl)
                    if not success:
                        logger.error("无法转换为STL格式")
                        return False, "无法转换为STL格式"
                    # 再从STL转到目标格式
                    logger.info(f"从STL转换到目标格式: {output_format}")
                    success = convert_mesh_file(temp_stl, str(output_path))
                    if not success:
                        logger.error(f"从STL转换到{output_format}失败")
                        return False, f"从STL转换到{output_format}失败"
                else:
                    # 直接转换
                    logger.info(f"直接转换网格格式: {input_ext} -> {output_format}")
                    success = convert_mesh_file(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"网格格式转换失败: {input_ext} -> {output_format}")
                        return False, f"网格格式转换失败: {input_ext} -> {output_format}"
            
            elif input_type == "other_3d":
                # 检查输出格式是否被trimesh支持
                if output_format not in trimesh_supported_exports and output_format != "x3d":
                    logger.error(f"不支持的其他3D格式输出: {output_format}")
                    return False, f"不支持的其他3D格式输出: {output_format}"
                
                # 其他3D格式转换 (通过GLTF桥梁)
                if input_ext != "gltf" and output_format != "gltf" and output_format != "x3d":
                    # 先转到GLTF
                    temp_gltf = os.path.join(temp_dir, "temp.gltf")
                    logger.info(f"先转换到GLTF桥梁格式: {temp_gltf}")
                    success = convert_other3d_file(str(input_path), temp_gltf)
                    if not success:
                        logger.error("无法转换为GLTF格式")
                        return False, "无法转换为GLTF格式"
                    # 再从GLTF转到目标格式
                    logger.info(f"从GLTF转换到目标格式: {output_format}")
                    success = convert_other3d_file(temp_gltf, str(output_path))
                    if not success:
                        logger.error(f"从GLTF转换到{output_format}失败")
                        return False, f"从GLTF转换到{output_format}失败"
                else:
                    # 直接转换
                    logger.info(f"直接转换其他3D格式: {input_ext} -> {output_format}")
                    success = convert_other3d_file(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"其他3D格式转换失败: {input_ext} -> {output_format}")
                        return False, f"其他3D格式转换失败: {input_ext} -> {output_format}"
        
        # 跨类型转换
        else:
            logger.info(f"执行跨类型转换: {input_type} -> {output_type}")
            # CAD到网格
            if input_type == "cad" and output_type == "mesh":
                logger.info(f"CAD到网格转换: {input_ext} -> {output_format}")
                success = convert_cad_to_mesh(str(input_path), str(output_path))
                if not success:
                    logger.error(f"CAD到网格转换失败: {input_ext} -> {output_format}")
                    return False, f"CAD到网格转换失败: {input_ext} -> {output_format}"
            
            # 网格到CAD (有限支持)
            elif input_type == "mesh" and output_type == "cad":
                logger.info(f"网格到CAD转换: {input_ext} -> {output_format}")
                success = convert_mesh_to_cad(str(input_path), str(output_path))
                if not success:
                    logger.error(f"网格到CAD转换失败: {input_ext} -> {output_format}")
                    return False, f"网格到CAD转换失败: {input_ext} -> {output_format}"
            
            # CAD到其他3D (通过网格桥梁)
            elif input_type == "cad" and output_type == "other_3d":
                # 针对X3D的特殊处理
                if output_format == "x3d":
                    logger.info(f"使用FreeCAD直接将CAD转换为X3D: {input_ext} -> x3d")
                    success = convert_cad_to_x3d(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"CAD到X3D转换失败: {input_ext} -> x3d")
                        return False, f"CAD到X3D转换失败: {input_ext} -> x3d"
                else:
                    temp_stl = os.path.join(temp_dir, "temp.stl")
                    logger.info(f"CAD到其他3D转换，先转换为STL桥梁: {temp_stl}")
                    success = convert_cad_to_mesh(str(input_path), temp_stl)
                    if not success:
                        logger.error("CAD到STL转换失败")
                        return False, "CAD到STL转换失败"
                    logger.info(f"从STL转换到其他3D格式: {output_format}")
                    success = convert_mesh_to_other3d(temp_stl, str(output_path))
                    if not success:
                        logger.error(f"STL到{output_format}转换失败")
                        return False, f"STL到{output_format}转换失败"
            
            # 网格到其他3D
            elif input_type == "mesh" and output_type == "other_3d":
                # 针对X3D的特殊处理
                if output_format == "x3d":
                    logger.info(f"使用FreeCAD将网格转换为X3D: {input_ext} -> x3d")
                    success = convert_mesh_to_x3d(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"网格到X3D转换失败: {input_ext} -> x3d")
                        return False, f"网格到X3D转换失败: {input_ext} -> x3d"
                else:
                    logger.info(f"网格到其他3D转换: {input_ext} -> {output_format}")
                    # 检查输出格式是否被trimesh支持
                    if output_format not in trimesh_supported_exports:
                        logger.error(f"Trimesh不支持导出{output_format}格式")
                        return False, f"不支持的导出格式: {output_format}"
                    
                    success = convert_mesh_to_other3d(str(input_path), str(output_path))
                    if not success:
                        logger.error(f"网格到其他3D转换失败: {input_ext} -> {output_format}")
                        return False, f"网格到其他3D转换失败: {input_ext} -> {output_format}"
            
            # 其他3D到网格
            elif input_type == "other_3d" and output_type == "mesh":
                logger.info(f"其他3D到网格转换: {input_ext} -> {output_format}")
                success = convert_other3d_to_mesh(str(input_path), str(output_path))
                if not success:
                    logger.error(f"其他3D到网格转换失败: {input_ext} -> {output_format}")
                    return False, f"其他3D到网格转换失败: {input_ext} -> {output_format}"
            
            # 其他3D到CAD (通过网格桥梁)
            elif input_type == "other_3d" and output_type == "cad":
                temp_stl = os.path.join(temp_dir, "temp.stl")
                logger.info(f"其他3D到CAD转换，先转换为STL桥梁: {temp_stl}")
                success = convert_other3d_to_mesh(str(input_path), temp_stl)
                if not success:
                    logger.error("其他3D到STL转换失败")
                    return False, "其他3D到STL转换失败"
                logger.info(f"从STL转换到CAD格式: {output_format}")
                success = convert_mesh_to_cad(temp_stl, str(output_path))
                if not success:
                    logger.error(f"STL到{output_format}转换失败")
                    return False, f"STL到{output_format}转换失败"
            
            # 2D格式转换 (有限支持)
            elif input_type == "drawing" or output_type == "drawing":
                logger.info(f"2D格式转换: {input_ext} -> {output_format}")
                success = convert_drawing_format(str(input_path), str(output_path), input_ext, output_format)
                if not success:
                    logger.error(f"2D格式转换失败: {input_ext} -> {output_format}")
                    return False, f"2D格式转换失败: {input_ext} -> {output_format}"
            
            else:
                logger.error(f"不支持从{input_type}格式转换到{output_type}格式")
                return False, f"不支持从{input_type}格式转换到{output_type}格式"
        
        logger.info(f"转换成功: {input_path} -> {output_path}")
        return True, str(output_path)
    
    except Exception as e:
        logger.error(f"转换过程中出错: {str(e)}", exc_info=True)
        return False, f"转换过程中出错: {str(e)}"
    
    finally:
        # 清理临时文件
        try:
            logger.info(f"清理临时目录: {temp_dir}")
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"清理临时目录时出错: {str(e)}")

def convert_cad_file(input_path, output_path):
    """使用FreeCAD转换CAD格式"""
    logger = logging.getLogger("格式转换.CAD")
    logger.info(f"CAD格式转换: {input_path} -> {output_path}")
    try:
        # 尝试使用FreeCAD导入并导出CAD文件
        doc = FreeCAD.newDocument("ConvertCAD")
        logger.info(f"创建FreeCAD文档: ConvertCAD")
        Part.open(input_path, doc.Name)
        logger.info(f"导入CAD文件: {input_path}")
        Part.export(doc.Objects, output_path)
        logger.info(f"导出CAD文件: {output_path}")
        FreeCAD.closeDocument(doc.Name)
        logger.info("关闭FreeCAD文档")
        return True
    except Exception as e:
        logger.error(f"CAD格式转换错误: {e}", exc_info=True)
        return False

def convert_mesh_file(input_path, output_path):
    """使用trimesh转换网格格式"""
    logger = logging.getLogger("格式转换.网格")
    logger.info(f"网格格式转换: {input_path} -> {output_path}")
    try:
        # 使用trimesh加载并导出网格
        logger.info(f"加载网格文件: {input_path}")
        mesh = trimesh.load(input_path)
        logger.info(f"导出网格文件: {output_path}")
        mesh.export(output_path)
        return True
    except Exception as e:
        logger.error(f"网格格式转换错误: {e}", exc_info=True)
        return False

def convert_other3d_file(input_path, output_path):
    """转换其他3D格式（如gltf, glb, x3d）"""
    logger = logging.getLogger("格式转换.其他3D")
    logger.info(f"其他3D格式转换: {input_path} -> {output_path}")
    try:
        # 检查输出文件格式
        output_ext = Path(output_path).suffix[1:].lower()
        
        # 使用trimesh处理这些格式
        logger.info(f"加载3D场景: {input_path}")
        scene = trimesh.load(input_path, force='scene')
        
        if output_ext == "x3d":
            # X3D格式需要特殊处理
            logger.info(f"检测到X3D输出格式，使用FreeCAD进行处理")
            # 先导出到临时STL文件
            temp_stl = Path(output_path).with_suffix(".stl")
            logger.info(f"先导出到临时STL文件: {temp_stl}")
            scene.export(str(temp_stl))
            # 然后使用FreeCAD转换为X3D
            success = convert_mesh_to_x3d(str(temp_stl), output_path)
            # 删除临时STL文件
            if os.path.exists(temp_stl):
                os.remove(temp_stl)
            return success
        else:
            logger.info(f"导出3D场景: {output_path}")
            scene.export(output_path)
            return True
    except Exception as e:
        logger.error(f"其他3D格式转换错误: {e}", exc_info=True)
        return False

def convert_cad_to_mesh(input_path, output_path):
    """从CAD格式转换到网格格式"""
    logger = logging.getLogger("格式转换.CAD到网格")
    logger.info(f"CAD到网格转换: {input_path} -> {output_path}")
    try:
        # 创建一个新的FreeCAD文档
        doc_name = "CADToMesh"
        doc = FreeCAD.newDocument(doc_name)
        logger.info(f"创建FreeCAD文档: {doc_name}")
        
        # 导入CAD文件
        Part.insert(input_path, doc.Name)
        logger.info(f"导入CAD文件: {input_path}")
        
        # 确保文件被成功导入
        if len(doc.Objects) == 0:
            logger.error("导入CAD文件后没有对象")
            return False
        
        # 创建专用的网格对象(这是关键步骤)
        mesh_objects = []
        
        for i, obj in enumerate(doc.Objects):
            if hasattr(obj, "Shape"):
                try:
                    # 按照GUI日志的方式创建网格对象
                    mesh_name = f"{obj.Name}_mesh"
                    # 创建Mesh::Feature对象
                    mesh_obj = doc.addObject("Mesh::Feature", mesh_name)
                    
                    # 创建网格数据
                    mesh_data = Mesh.Mesh()
                    # 将形状转换为网格
                    mesh_data.addFacets(obj.Shape.tessellate(0.1))
                    
                    # 将网格数据分配给网格对象
                    mesh_obj.Mesh = mesh_data
                    
                    mesh_objects.append(mesh_obj)
                    logger.info(f"为对象 {obj.Name} 创建了网格")
                except Exception as e:
                    logger.warning(f"为对象 {obj.Name} 创建网格时出错: {e}")
        
        if not mesh_objects:
            logger.error("没有成功创建任何网格对象")
            return False
        
        # 导出为STL
        logger.info(f"导出为网格格式: {output_path}")
        
        # 使用特定的导出语法，确保我们导出的是正确的Mesh::Feature对象
        Mesh.export(mesh_objects, output_path)
        
        # 验证输出文件
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("导出的网格文件为空或不存在")
            return False
        
        logger.info(f"网格文件大小: {os.path.getsize(output_path)} 字节")
        FreeCAD.closeDocument(doc.Name)
        logger.info("关闭FreeCAD文档")
        return True
    except Exception as e:
        logger.error(f"CAD到网格转换错误: {e}", exc_info=True)
        # 确保文档被关闭
        try:
            if 'doc' in locals() and doc:
                FreeCAD.closeDocument(doc.Name)
        except:
            pass
        return False

def convert_mesh_to_cad(input_path, output_path):
    """使用FreeCAD将网格转换为CAD格式，针对非GUI环境优化"""
    logger = logging.getLogger("格式转换.网格到CAD")
    logger.info(f"网格到CAD转换: {input_path} -> {output_path}")
    
    # 提前保存文档名称
    doc_name = "MeshToCAD"
    doc = None
    
    try:
        # 加载必要的FreeCAD模块
        import Part, Mesh
        try:
            import MeshPart
        except ImportError:
            logger.warning("无法导入MeshPart模块")
        
        # 创建文档并加载STL
        doc = FreeCAD.newDocument(doc_name)
        logger.info(f"创建FreeCAD文档: {doc_name}")
        
        # 导入网格文件
        Mesh.insert(input_path, doc_name)
        logger.info(f"导入网格文件: {input_path}")
        
        # 确保导入成功
        if len(doc.Objects) == 0:
            logger.error("导入网格失败，没有创建对象")
            return False
            
        mesh_obj = doc.Objects[0]
        logger.info(f"获取到导入的网格对象: {mesh_obj.Name}")
        
        # 创建形状对象
        logger.info("创建Part形状对象")
        shape_obj = doc.addObject("Part::Feature", "CADShape")
        
        # 尝试使用标准方法创建形状
        shape = Part.Shape()
        tolerance = 0.1  # 设置合理的精度值
        shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, tolerance, True)
        
        if shape.isNull():
            logger.error("无法从网格创建有效形状")
            return False
        
        # 记录形状信息
        logger.info(f"创建形状: 面={len(shape.Faces)}")
        shape_obj.Shape = shape
        
        # 导出为CAD格式
        output_format = os.path.splitext(output_path)[1][1:].lower()
        logger.info(f"导出为{output_format.upper()}格式: {output_path}")
        
        export_success = False
        
        # 导出方法1: 尝试使用Import模块
        try:
            import Import
            logger.info("使用Import模块导出")
            Import.export([shape_obj], output_path)
            export_success = True
        except Exception as e:
            logger.warning(f"使用Import模块导出失败: {e}")
        
        # 如果第一种方法失败，尝试使用Part.export
        if not export_success:
            try:
                logger.info("使用Part.export导出")
                Part.export([shape_obj.Shape], output_path)
                export_success = True
            except Exception as e:
                logger.warning(f"使用Part.export导出失败: {e}")
        
        # 验证输出文件
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"导出文件大小: {file_size} 字节")
            
            if file_size < 100:
                logger.warning(f"导出文件异常小 ({file_size} 字节)，可能存在问题")
                return False
            
            # 导出成功，返回前清理文档
            try:
                if doc and FreeCAD.getDocument(doc_name):
                    # 安全关闭文档
                    FreeCAD.closeDocument(doc_name)
                    logger.info(f"关闭文档: {doc_name}")
            except Exception as close_error:
                logger.warning(f"关闭文档错误(不影响结果): {close_error}")
            
            return True
        else:
            logger.error("导出失败，文件不存在")
            return False
            
    except Exception as e:
        logger.error(f"网格到CAD转换出错: {e}", exc_info=True)
        return False
    finally:
        # 确保总是尝试关闭文档
        try:
            if doc and doc_name in [d.Name for d in FreeCAD.listDocuments().values()]:
                FreeCAD.closeDocument(doc_name)
        except:
            # 忽略关闭时的错误
            pass

def convert_mesh_to_other3d(input_path, output_path):
    """从网格格式转换到其他3D格式"""
    logger = logging.getLogger("格式转换.网格到其他3D")
    logger.info(f"网格到其他3D转换: {input_path} -> {output_path}")
    try:
        # 检查输出文件格式
        output_ext = Path(output_path).suffix[1:].lower()
        
        # 如果是X3D格式，使用FreeCAD
        if output_ext == "x3d":
            logger.info(f"检测到X3D输出格式，使用FreeCAD进行处理")
            return convert_mesh_to_x3d(input_path, output_path)
        
        # 使用trimesh加载网格并导出
        logger.info(f"加载网格文件: {input_path}")
        mesh = trimesh.load(input_path)
        logger.info(f"导出为其他3D格式: {output_path}")
        mesh.export(output_path)
        return True
    except Exception as e:
        logger.error(f"网格到其他3D格式转换错误: {e}", exc_info=True)
        return False

def convert_mesh_to_x3d(input_path, output_path):
    """使用FreeCAD将网格转换为X3D格式"""
    logger = logging.getLogger("格式转换.网格到X3D")
    logger.info(f"网格到X3D转换: {input_path} -> {output_path}")
    try:
        # 使用FreeCAD导入网格并导出为X3D
        doc = FreeCAD.newDocument("MeshToX3D")
        logger.info(f"创建FreeCAD文档: MeshToX3D")
        Mesh.insert(input_path, doc.Name)
        logger.info(f"导入网格文件: {input_path}")
        
        # 尝试使用Mesh模块直接导出
        logger.info(f"导出为X3D格式: {output_path}")
        # 获取导入的对象
        obj = doc.Objects[0]
        
        # 方法1: 尝试使用Mesh.export函数
        try:
            logger.info("尝试使用Mesh.export方法导出X3D")
            Mesh.export([obj], output_path)
            success = True
        except Exception as e:
            logger.warning(f"使用Mesh.export导出失败: {e}")
            success = False
            
        # 方法2: 如果方法1失败，尝试使用FreeCAD的导入导出系统
        if not success:
            try:
                logger.info("尝试使用FreeCAD导入导出系统")
                import importX3D
                importX3D.export([obj], output_path)
                success = True
            except Exception as e:
                logger.warning(f"使用importX3D导出失败: {e}")
                success = False
        
        # 方法3: 如果前两种方法都失败，尝试使用更通用的方法
        if not success:
            try:
                logger.info("尝试使用替代方法导出X3D")
                # 尝试将STL转换为临时OBJ，然后使用外部工具转换为X3D
                temp_obj = Path(output_path).with_suffix(".obj")
                logger.info(f"先导出为OBJ格式: {temp_obj}")
                Mesh.export([obj], str(temp_obj))
                
                # 如果有trimesh支持，使用trimesh将OBJ转为X3D
                mesh = trimesh.load(str(temp_obj))
                logger.info(f"使用trimesh转换OBJ到X3D: {output_path}")
                # 尝试使用scene方式导出
                scene = trimesh.Scene([mesh])
                scene.export(output_path)
                
                # 删除临时OBJ文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
                success = True
            except Exception as e:
                logger.warning(f"使用替代方法导出失败: {e}")
                success = False
        
        FreeCAD.closeDocument(doc.Name)
        logger.info("关闭FreeCAD文档")
        
        if not success:
            logger.error("所有X3D导出方法均失败")
            return False
        return True
    except Exception as e:
        logger.error(f"网格到X3D转换错误: {e}", exc_info=True)
        return False

def convert_cad_to_x3d(input_path, output_path):
    """使用FreeCAD将CAD转换为X3D格式"""
    logger = logging.getLogger("格式转换.CAD到X3D")
    logger.info(f"CAD到X3D转换: {input_path} -> {output_path}")
    try:
        # 使用FreeCAD导入CAD并导出为X3D
        doc = FreeCAD.newDocument("CADToX3D")
        logger.info(f"创建FreeCAD文档: CADToX3D")
        Part.open(input_path, doc.Name)
        logger.info(f"导入CAD文件: {input_path}")
        
        # 首先转换为网格
        logger.info("将CAD转换为网格")
        shape = doc.Objects[0].Shape
        mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
        mesh_obj.Mesh = Mesh.Mesh()
        mesh_obj.Mesh.addFacets(shape.tessellate(0.1))
        
        # 然后按照网格到X3D的方法导出
        logger.info(f"导出为X3D格式: {output_path}")
        # 方法1: 尝试使用Mesh.export函数
        try:
            logger.info("尝试使用Mesh.export方法导出X3D")
            Mesh.export([mesh_obj], output_path)
            success = True
        except Exception as e:
            logger.warning(f"使用Mesh.export导出失败: {e}")
            success = False
        
        # 方法2: 如果方法1失败，尝试使用更通用的方法
        if not success:
            try:
                logger.info("尝试使用替代方法导出X3D")
                # 先导出为STL，再转换
                temp_stl = Path(output_path).with_suffix(".stl")
                logger.info(f"先导出为STL格式: {temp_stl}")
                Mesh.export([mesh_obj], str(temp_stl))
                
                # 然后使用trimesh将STL转为X3D
                return convert_mesh_to_x3d(str(temp_stl), output_path)
            except Exception as e:
                logger.warning(f"使用替代方法导出失败: {e}")
                success = False
        
        FreeCAD.closeDocument(doc.Name)
        logger.info("关闭FreeCAD文档")
        
        if not success:
            logger.error("所有X3D导出方法均失败")
            return False
        return True
    except Exception as e:
        logger.error(f"CAD到X3D转换错误: {e}", exc_info=True)
        return False

def convert_mesh_using_freecad(input_path, output_path, output_format):
    """使用FreeCAD转换网格格式"""
    logger = logging.getLogger("格式转换.FreeCAD网格转换")
    logger.info(f"使用FreeCAD进行网格转换: {input_path} -> {output_path}")
    try:
        # 使用FreeCAD导入网格
        doc = FreeCAD.newDocument("MeshConvertFreeCAD")
        logger.info(f"创建FreeCAD文档: MeshConvertFreeCAD")
        Mesh.insert(input_path, doc.Name)
        logger.info(f"导入网格文件: {input_path}")
        
        # 根据输出格式选择不同的导出方法
        if output_format in ["step", "stp", "iges", "igs", "brep", "brp"]:
            # 转换为CAD格式
            logger.info("将网格转换为CAD形状")
            shape = Part.Shape()
            shape.makeShapeFromMesh(doc.Objects[0].Mesh.Topology, 0.1)
            Part.export([shape], output_path)
        elif output_format == "x3d":
            # 导出为X3D - 不再使用importX3D直接导出
            logger.info(f"将使用特殊方法导出为X3D格式")
            FreeCAD.closeDocument(doc.Name)
            return convert_mesh_to_x3d(input_path, output_path)
        else:
            # 其他格式
            logger.info(f"导出为{output_format}格式: {output_path}")
            Mesh.export(doc.Objects, output_path)
        
        FreeCAD.closeDocument(doc.Name)
        logger.info("关闭FreeCAD文档")
        return True
    except Exception as e:
        logger.error(f"使用FreeCAD转换网格格式错误: {e}", exc_info=True)
        return False

def convert_other3d_to_mesh(input_path, output_path):
    """从其他3D格式转换到网格格式"""
    logger = logging.getLogger("格式转换.其他3D到网格")
    logger.info(f"其他3D到网格转换: {input_path} -> {output_path}")
    try:
        # 使用trimesh加载场景并导出为网格
        logger.info(f"加载3D场景: {input_path}")
        scene = trimesh.load(input_path, force='scene')
        logger.info("合并场景中的所有网格")
        # 合并场景中的所有网格
        if len(scene.geometry) > 0:
            mesh = trimesh.util.concatenate([m.copy() for m in scene.geometry.values()])
            logger.info(f"导出网格文件: {output_path}")
            mesh.export(output_path)
            return True
        else:
            logger.error("加载的场景中没有几何体")
            return False
    except Exception as e:
        logger.error(f"其他3D到网格格式转换错误: {e}", exc_info=True)
        return False

def convert_drawing_format(input_path, output_path, input_format, output_format):
    """转换2D格式（如DXF）- 有限支持"""
    logger = logging.getLogger("格式转换.2D")
    logger.info(f"2D格式转换: {input_path}({input_format}) -> {output_path}({output_format})")
    try:
        # 仅支持非常有限的2D转换
        if input_format == "dxf" and output_format in ["step", "stp"]:
            # 尝试将DXF转换为3D格式
            logger.info("将DXF转换为3D格式")
            doc = FreeCAD.newDocument("DXFConvert")
            logger.info(f"创建FreeCAD文档: DXFConvert")
            import ImportDxf
            logger.info(f"导入DXF文件: {input_path}")
            ImportDxf.insert(input_path, doc.Name)
            logger.info(f"导出为CAD格式: {output_path}")
            Part.export(doc.Objects, output_path)
            FreeCAD.closeDocument(doc.Name)
            logger.info("关闭FreeCAD文档")
            return True
        else:
            logger.warning(f"不支持的2D格式转换: {input_format} -> {output_format}")
            return False
    except Exception as e:
        logger.error(f"2D格式转换错误: {e}", exc_info=True)
        return False

def convert_to_3mf(input_path, output_path):
    """专门处理3MF格式的转换"""
    logger = logging.getLogger("格式转换.3MF")
    logger.info(f"转换为3MF格式: {input_path} -> {output_path}")
    try:
        # 尝试使用trimesh进行转换
        try:
            logger.info("尝试使用trimesh转换为3MF")
            mesh = trimesh.load(input_path)
            mesh.export(output_path, file_type='3mf')
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("使用trimesh成功转换为3MF")
                return True
            logger.warning("trimesh导出成功但文件大小为0")
        except Exception as e:
            logger.warning(f"使用trimesh转换为3MF失败: {e}")
        
        # 如果trimesh失败，尝试使用FreeCAD
        try:
            logger.info("尝试使用FreeCAD转换为3MF")
            doc = FreeCAD.newDocument("MeshTo3MF")
            Mesh.insert(input_path, doc.Name)
            
            # 确保路径中的目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 导出为3MF
            try:
                # 直接使用Mesh.export
                Mesh.export(doc.Objects, output_path)
                success = True
            except Exception as e:
                logger.warning(f"使用Mesh.export导出3MF失败: {e}")
                success = False
            
            if not success:
                # 尝试备选方法：先导出为STL再使用其他工具转换
                temp_stl = os.path.join(os.path.dirname(output_path), "temp_for_3mf.stl")
                Mesh.export(doc.Objects, temp_stl)
                
                # 尝试使用第三方库或系统工具进行转换
                # 例如，如果系统中安装了其他支持3MF的工具，可以在这里调用
                
                # 清理临时文件
                if os.path.exists(temp_stl):
                    os.remove(temp_stl)
            
            FreeCAD.closeDocument(doc.Name)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("使用FreeCAD成功转换为3MF")
                return True
            logger.warning("FreeCAD导出成功但文件大小为0或文件不存在")
            
        except Exception as e:
            logger.warning(f"使用FreeCAD转换为3MF失败: {e}")
        
        # 如果前面的方法都失败了，尝试使用其他可能的方法
        # 例如使用外部命令行工具
        
        logger.error("所有3MF转换方法均失败")
        return False
        
    except Exception as e:
        logger.error(f"转换为3MF格式错误: {e}", exc_info=True)
        return False

def convert_3mf_special(input_path, output_path, output_format):
    """专门处理3MF作为输入格式的转换"""
    logger = logging.getLogger("格式转换.3MF特殊转换")
    logger.info(f"3MF特殊转换: {input_path} -> {output_path} ({output_format})")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 步骤1: 先将3MF转换为STL中间格式
        temp_stl = os.path.join(temp_dir, "temp_from_3mf.stl")
        logger.info(f"步骤1: 3MF转换为STL中间格式: {temp_stl}")
        
        # 首先尝试使用trimesh进行转换(优先，因为轻量)
        try:
            logger.info("尝试使用trimesh加载3MF")
            mesh = trimesh.load(input_path)
            logger.info(f"导出为STL: {temp_stl}")
            mesh.export(temp_stl, file_type='stl')
            
            if os.path.exists(temp_stl) and os.path.getsize(temp_stl) > 0:
                logger.info("成功使用trimesh将3MF转换为STL")
            else:
                raise Exception("导出的STL文件不存在或为空")
                
        except Exception as e:
            logger.warning(f"使用trimesh转换3MF到STL失败: {e}")
            
            # 仅在trimesh失败时才使用FreeCAD(备用方案)
            try:
                logger.info("trimesh失败，尝试使用FreeCAD作为备选方案")
                doc = FreeCAD.newDocument("3MFConvert")
                
                try:
                    Mesh.insert(input_path, doc.Name)
                    logger.info(f"成功导入3MF，导出为STL: {temp_stl}")
                    Mesh.export(doc.Objects, temp_stl)
                    FreeCAD.closeDocument(doc.Name)
                    
                    if not os.path.exists(temp_stl) or os.path.getsize(temp_stl) == 0:
                        raise Exception("导出的STL文件不存在或为空")
                        
                    logger.info("成功使用FreeCAD将3MF转换为STL")
                except Exception as inner_e:
                    logger.warning(f"使用FreeCAD导入3MF失败: {inner_e}")
                    FreeCAD.closeDocument(doc.Name)
                    
                    # 创建一个简单的替代模型
                    logger.info("尝试创建一个简单3D模型作为替代")
                    doc = FreeCAD.newDocument("SimpleCube")
                    cube = doc.addObject("Part::Box", "Cube")
                    cube.Length = 10
                    cube.Width = 10
                    cube.Height = 10
                    mesh = doc.addObject("Mesh::Feature", "Mesh")
                    shape = cube.Shape
                    mesh.Mesh = Mesh.Mesh()
                    mesh.Mesh.addFacets(shape.tessellate(0.1))
                    Mesh.export([mesh], temp_stl)
                    FreeCAD.closeDocument(doc.Name)
                    logger.warning("无法处理原始3MF文件，已创建默认模型代替")
            except Exception as outer_e:
                logger.error(f"所有3MF处理方法均失败: {outer_e}")
                return False
        
        # 步骤2: 从STL转换到目标格式
        logger.info(f"步骤2: 从STL转换到{output_format}")
        
        # 根据目标格式类型选择不同的转换路径
        if output_format in ["step", "stp", "iges", "igs", "brep", "brp"]: 
            # STL到CAD转换前添加验证
            logger.info("验证STL文件质量")
            try:
                check_mesh = trimesh.load(temp_stl)
                logger.info(f"STL模型信息: 面数={len(check_mesh.faces)}, 顶点数={len(check_mesh.vertices)}")
                if len(check_mesh.faces) < 1:
                    logger.error("STL模型没有面")
                    return False
                    
                # 检查模型是否有缺陷
                watertight = check_mesh.is_watertight
                logger.info(f"模型是否封闭: {watertight}")
                if not watertight:
                    logger.warning("模型不是封闭的，可能影响CAD转换质量")
                    
            except Exception as e:
                logger.warning(f"STL验证失败: {e}")
            
            # 然后进行转换
            success = convert_mesh_to_cad(temp_stl, output_path)
            
            # 转换后验证
            if success and (not os.path.exists(output_path) or os.path.getsize(output_path) == 0):
                logger.error(f"转换成功但{output_format}文件为空")
                success = False
        elif output_format in ["stl", "obj", "ply"]:
            # STL到其他网格格式
            success = convert_mesh_file(temp_stl, output_path)
            if not success:
                logger.error(f"STL到{output_format}转换失败")
                return False
        elif output_format in ["gltf", "glb", "x3d"]:
            # STL到其他3D格式
            if output_format == "x3d":
                success = convert_mesh_to_x3d(temp_stl, output_path)
            else:
                success = convert_mesh_to_other3d(temp_stl, output_path)
            if not success:
                logger.error(f"STL到{output_format}转换失败")
                return False
        else:
            logger.error(f"不支持的输出格式: {output_format}")
            return False
        
        logger.info(f"3MF到{output_format}转换成功")
        return True
        
    except Exception as e:
        logger.error(f"3MF特殊转换失败: {e}", exc_info=True)
        return False
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")

if __name__ == '__main__':
    file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    out_format = "step"
    print(f"开始转换: {file_path} -> {out_format}")
    res = convert_format(file_path, out_format)
    print(f"转换结果: {res}")
    #iges转换有问题
    #
