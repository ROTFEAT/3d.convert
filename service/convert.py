#!/usr/bin/env python
# -*- coding: utf-8 -*-
from config import *
import os
import sys
import FreeCAD
import Part
try:
    import trimesh  # 导入trimesh库用于网格处理
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False
    print("警告: 未安装trimesh库，部分网格转换功能可能受限")


def convert_file(input_filename, output_format):
    """
    使用 FreeCAD 将输入文件转换为指定格式

    参数:
        input_filename (str): 输入文件名（包含完整路径）
        output_format (str): 输出文件格式（不含点，例如 'obj' 而不是 '.obj'）

    返回:
        bool: 转换成功返回 True，否则返回 False
        str: 输出文件的完整路径（成功时）或错误信息（失败时）
    """
    # 确保输入和输出目录存在
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    # 检查输入文件是否包含完整路径
    if os.path.dirname(input_filename):
        # 已经是完整路径
        input_path = input_filename
    else:
        # 只有文件名，添加INPUT_DIR路径
        input_path = os.path.join(INPUT_DIR, input_filename)

    if not os.path.exists(input_path):
        error_msg = f"错误: 输入文件 '{input_path}' 不存在"
        print(error_msg)
        return False, error_msg

    # 获取文件名（不含扩展名）用于输出
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{base_name}.{output_format.lower()}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        # 创建新文档
        doc = FreeCAD.newDocument("Conversion")

        # 使用非GUI方式导入文件
        input_ext = os.path.splitext(input_filename)[1].lower()

        # 支持的输入格式映射
        input_formats = {
            '.step': lambda path, name: Part.insert(path, name),
            '.stp': lambda path, name: Part.insert(path, name),
            '.iges': lambda path, name: Part.insert(path, name),
            '.igs': lambda path, name: Part.insert(path, name),
            '.brep': lambda path, name: Part.insert(path, name),
            '.brp': lambda path, name: Part.insert(path, name),
            '.sat': lambda path, name: Part.insert(path, name),
            '.x_t': lambda path, name: import_module_file('ImportXCAF', path, name),
            '.x_b': lambda path, name: import_module_file('ImportXCAF', path, name),
            '.3dxml': lambda path, name: import_module_file('Import3dxml', path, name),
            '.catpart': lambda path, name: import_module_file('ImportCatia', path, name),
            '.prt': lambda path, name: import_module_file('ImportNX', path, name),
            '.sldprt': lambda path, name: import_module_file('ImportSolidWorks', path, name),
            '.ipt': lambda path, name: import_module_file('ImportInventor', path, name),
            '.jt': lambda path, name: import_module_file('ImportJT', path, name),
            '.stl': lambda path, name: import_module_file('Mesh', path, name, is_mesh=True),
            '.3mf': lambda path, name: import_module_file('Import3MF', path, name),
            '.dxf': lambda path, name: import_module_file('ImportDXF', path, name),
        }

        def import_module_file(module_name, file_path, doc_name, is_mesh=False):
            """尝试导入特定模块的文件"""
            try:
                module = __import__(module_name)
                if is_mesh:
                    # 对于网格文件，使用特殊处理
                    mesh = module.Mesh(file_path)
                    mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
                    mesh_obj.Mesh = mesh
                else:
                    # 对于其他格式，尝试使用通用导入方法
                    if hasattr(module, 'insert'):
                        module.insert(file_path, doc_name)
                    elif hasattr(module, 'open'):
                        module.open(file_path)
                    else:
                        raise ImportError(f"模块 {module_name} 没有 insert 或 open 方法")
            except Exception as e:
                print(f"警告: 使用 {module_name} 导入失败: {str(e)}")
                # 尝试使用 Part 模块作为备选
                try:
                    Part.insert(file_path, doc_name)
                except:
                    raise ImportError(f"无法导入文件 {file_path}")

        # 尝试导入文件
        if input_ext in input_formats:
            input_formats[input_ext](input_path, doc.Name)
        else:
            # 对于未知格式，尝试使用通用方法
            try:
                Part.insert(input_path, doc.Name)
            except:
                try:
                    import Mesh
                    mesh = Mesh.Mesh(input_path)
                    mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
                    mesh_obj.Mesh = mesh
                except Exception as e:
                    error_msg = f"无法导入未知文件格式 {input_ext}: {str(e)}"
                    print(error_msg)
                    return False, error_msg

        # 检查是否成功导入了对象
        if len(doc.Objects) == 0:
            error_msg = "错误: 无法从输入文件中加载对象"
            print(error_msg)
            return False, error_msg

        # 获取所有对象
        objects = doc.Objects

        # 支持的输出格式映射
        output_format = output_format.lower()

        # 定义导出函数
        def export_step(objs, path):
            Part.export(objs, path)

        def export_iges(objs, path):
            Part.export(objs, path)

        def export_brep(objs, path):
            Part.export(objs, path)

        def export_stl(objs, path):
            import Mesh
            shapes = []
            for obj in objs:
                if hasattr(obj, "Shape"):
                    shapes.append(obj.Shape)

            if shapes:
                mesh = Mesh.Mesh()
                for shape in shapes:
                    mesh.addFacets(shape.tessellate(0.1))
                mesh.write(path)
            else:
                raise Exception("无法创建网格")

        def export_obj(objs, path):
            import Mesh
            shapes = []
            for obj in objs:
                if hasattr(obj, "Shape"):
                    shapes.append(obj.Shape)

            if shapes:
                mesh = Mesh.Mesh()
                for shape in shapes:
                    mesh.addFacets(shape.tessellate(0.1))
                mesh.write(path)
            else:
                raise Exception("无法创建网格")

        def export_3mf(objs, path):
            try:
                import Import3MF
                Import3MF.export(objs, path)
            except:
                # 备选方案：转换为网格后导出
                export_stl(objs, path[:-4] + ".stl")
                import os
                os.rename(path[:-4] + ".stl", path)

        def export_dxf(objs, path):
            """
            将对象导出为DXF格式
            使用 TechDraw 模块作为主要方法
            """
            try:
                import TechDraw
                import Part

                # 创建一个临时文档来处理绘图
                temp_doc = FreeCAD.newDocument("TempDrawing")

                # 创建一个页面
                page = temp_doc.addObject('TechDraw::DrawPage', 'Page')
                template = temp_doc.addObject('TechDraw::DrawSVGTemplate', 'Template')
                template.Template = ""  # 使用空模板
                page.Template = template

                exported = False
                for obj in objs:
                    if hasattr(obj, "Shape"):
                        try:
                            # 创建视图
                            view = temp_doc.addObject('TechDraw::DrawViewPart', 'View')

                            # 复制形状到临时文档
                            temp_shape = temp_doc.addObject("Part::Feature", "TempShape")
                            temp_shape.Shape = obj.Shape.copy()

                            view.Source = [temp_shape]
                            view.Direction = (0.0, 0.0, 1.0)  # 俯视图
                            view.Scale = 1.0
                            view.X = 100
                            view.Y = 100

                            # 将视图添加到页面
                            page.addView(view)
                            temp_doc.recompute()

                            # 导出为DXF
                            TechDraw.writeDXFPage(page, path)
                            exported = True
                            break  # 成功导出一个对象后退出

                        except Exception as view_error:
                            print(f"视图创建失败: {str(view_error)}")
                            continue

                # 清理临时文档
                FreeCAD.closeDocument("TempDrawing")

                if not exported:
                    raise Exception("没有成功导出任何对象")

            except Exception as e:
                print(f"TechDraw模块导出失败: {str(e)}")
                try:
                    # 尝试使用 Draft 模块
                    import Draft

                    # 创建一个新的临时文档
                    temp_doc = FreeCAD.newDocument("TempDraft")

                    exported = False
                    for obj in objs:
                        if hasattr(obj, "Shape"):
                            try:
                                # 复制对象到临时文档
                                temp_shape = temp_doc.addObject("Part::Feature", "TempShape")
                                temp_shape.Shape = obj.Shape.copy()
                                temp_doc.recompute()

                                # 使用 Draft 导出
                                Draft.export([temp_shape], path)
                                exported = True
                                break
                            except Exception as draft_error:
                                print(f"Draft导出对象失败: {str(draft_error)}")
                                continue

                    # 清理临时文档
                    FreeCAD.closeDocument("TempDraft")

                    if not exported:
                        raise Exception("Draft模块无法导出任何对象")

                except Exception as draft_error:
                    print(f"Draft模块导出失败: {str(draft_error)}")
                    try:
                        # 最后尝试使用 Part 模块导出为 IGES 然后转换
                        shapes = []
                        for obj in objs:
                            if hasattr(obj, "Shape"):
                                shapes.append(obj.Shape)

                        if shapes:
                            # 导出为 IGES
                            temp_iges = path[:-4] + ".igs"
                            Part.export(shapes, temp_iges)

                            # 使用 dxf_converter 转换（需要安装）
                            try:
                                import subprocess
                                subprocess.run(['dxf_converter', temp_iges, path], check=True)

                                # 清理临时文件
                                if os.path.exists(temp_iges):
                                    os.remove(temp_iges)

                            except Exception as conv_error:
                                print(f"DXF转换失败: {str(conv_error)}")
                                if os.path.exists(temp_iges):
                                    print(f"已生成IGES文件: {temp_iges}")
                                raise Exception("无法完成DXF转换")
                        else:
                            raise Exception("没有可以导出的形状")

                    except Exception as part_error:
                        print(f"Part模块导出失败: {str(part_error)}")
                        raise Exception("无法导出为DXF格式")

        def export_ply(objs, path):
            """导出为 PLY 格式"""
            try:
                import Mesh
                shapes = []
                for obj in objs:
                    if hasattr(obj, "Shape"):
                        shapes.append(obj.Shape)

                if shapes:
                    mesh = Mesh.Mesh()
                    for shape in shapes:
                        mesh.addFacets(shape.tessellate(0.1))
                    mesh.write(path, "PLY")
                else:
                    raise Exception("无法创建网格")
            except Exception as e:
                print(f"PLY导出错误: {str(e)}")
                raise

        def export_gltf(objs, path):
            """导出为 glTF 格式"""
            try:
                import importGLTF
                importGLTF.export(objs, path)
            except:
                # 备选方案：转换为 OBJ 后使用外部工具转换
                try:
                    temp_obj = path[:-5] + ".obj"
                    export_obj(objs, temp_obj)
                    # 这里可以添加使用外部工具将 OBJ 转换为 GLTF 的代码
                    if os.path.exists(temp_obj):
                        os.remove(temp_obj)
                except Exception as e:
                    print(f"GLTF导出错误: {str(e)}")
                    raise

        def export_x3d(objs, path):
            """导出为 X3D 格式"""
            try:
                import importX3D
                importX3D.export(objs, path)
            except:
                # 备选方案：使用 Mesh 模块
                try:
                    import Mesh
                    shapes = []
                    for obj in objs:
                        if hasattr(obj, "Shape"):
                            shapes.append(obj.Shape)

                    if shapes:
                        mesh = Mesh.Mesh()
                        for shape in shapes:
                            mesh.addFacets(shape.tessellate(0.1))
                        mesh.write(path, "X3D")
                    else:
                        raise Exception("无法创建网格")
                except Exception as e:
                    print(f"X3D导出错误: {str(e)}")
                    raise

        # 输出格式映射
        output_formats = {
            'step': export_step,
            'stp': export_step,
            'iges': export_iges,
            'igs': export_iges,
            'brep': export_brep,
            'brp': export_brep,
            'stl': export_stl,
            'obj': export_obj,
            '3mf': export_3mf,
            'dxf': export_dxf,
            'berp': export_brep,
            'ply': export_ply,
            'gltf': export_gltf,
            'glb': export_gltf,
            'x3d': export_x3d
        }

        # 在 convert_file 函数中添加不支持的格式列表
        UNSUPPORTED_EXPORT_FORMATS = {
            'sat': 'ACIS SAT 格式需要 ACIS 许可',
            'x_t': 'Parasolid X_T 格式需要 Parasolid 许可',
            'x_b': 'Parasolid X_B 格式需要 Parasolid 许可',
            '3dxml': 'CATIA 3DXML 格式需要 CATIA 许可',
            'catpart': 'CATIA Part 格式需要 CATIA 许可',
            'prt': 'NX PRT 格式需要 Siemens NX 许可',
            'sldprt': 'SolidWorks Part 格式需要 SolidWorks 许可',
            'ipt': 'Inventor Part 格式需要 Inventor 许可',
            'jt': 'JT 格式需要 Siemens PLM 许可'
        }

        # 添加实验性/有限支持的格式
        EXPERIMENTAL_FORMATS = {
            'bms': '实验性支持，可能需要额外插件',
            'xdmf': '实验性支持，可能需要额外插件',
            'asc': '实验性支持，可能需要额外插件',
            'pcd': '实验性支持，可能需要额外插件',
            'pdf': '仅支持 2D 导出',
            'oca': '实验性支持，可能需要额外插件',
            'csg': '实验性支持，可能需要额外插件',
            'scad': '实验性支持，可能需要额外插件',
            'ast': '实验性支持，可能需要额外插件',
            'dwg': '需要额外的 CAD 转换器支持'
        }

        # 执行导出
        if output_format in output_formats:
            output_formats[output_format](objects, output_path)
        elif output_format in UNSUPPORTED_EXPORT_FORMATS:
            error_msg = (f"不支持导出 {output_format.upper()} 格式: "
                        f"{UNSUPPORTED_EXPORT_FORMATS[output_format]}。"
                        f"建议导出为 STEP 格式")
            print(error_msg)
            return False, error_msg
        elif output_format in EXPERIMENTAL_FORMATS:
            error_msg = (f"格式 {output_format.upper()} {EXPERIMENTAL_FORMATS[output_format]}。"
                        f"建议使用其他格式")
            print(error_msg)
            return False, error_msg
        else:
            error_msg = f"未知的输出格式: {output_format}"
            print(error_msg)
            return False, error_msg

        success_msg = f"转换成功: '{input_filename}' -> '{output_filename}'"
        print(success_msg)
        FreeCAD.closeDocument("Conversion")
        return True, output_path

    except Exception as e:
        error_msg = f"转换过程中出错: {str(e)}"
        print(error_msg)
        if FreeCAD.ActiveDocument:
            FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
        return False, error_msg

def convert_file_pro(input_filename, output_format):
    """
    增强版CAD文件转换函数，使用中间格式策略
    
    参数:
        input_filename: 输入文件名或完整路径
        output_format: 输出格式
        
    返回:
        (success, result): 布尔成功标志和结果/错误信息
    """
    try:
        from config import INPUT_DIR, OUTPUT_DIR, TMP_DIR
        
        # 检查输入文件是否包含完整路径
        if os.path.dirname(input_filename):
            # 已经是完整路径
            input_path = input_filename
        else:
            # 只有文件名，添加INPUT_DIR路径
            input_path = os.path.join(INPUT_DIR, input_filename)
            
        # 解析文件名和扩展名
        name, ext = os.path.splitext(os.path.basename(input_path))
        input_format = ext.lower()[1:]  # 去掉开头的点
        output_format = output_format.lower()
        
        print("\n" + "="*50)
        print(f"详细转换日志: {input_path} -> {output_format}")
        print("="*50)
        
        # 定义格式分类
        cad_formats = {'step', 'stp', 'iges', 'igs', 'brep', 'brp'}
        print_formats = {'stl', '3mf'}
        mesh_formats = {'obj', 'ply', 'gltf', 'glb', 'x3d'}
        
        # 确定输入和输出格式的类别
        input_category = ''
        if input_format in cad_formats:
            input_category = 'cad'
        elif input_format in print_formats:
            input_category = 'print'
        elif input_format in mesh_formats:
            input_category = 'mesh'
        else:
            # 默认视为CAD格式
            input_category = 'cad'
        
        output_category = ''
        if output_format in cad_formats:
            output_category = 'cad'
        elif output_format in print_formats:
            output_category = 'print'
        elif output_format in mesh_formats:
            output_category = 'mesh'
        else:
            # 未知格式视为CAD格式（尝试最高质量转换）
            output_category = 'cad'
        
        print(f"[类别分析] 输入: {input_format} (属于{input_category}类)")
        print(f"[类别分析] 输出: {output_format} (属于{output_category}类)")
        
        # 如果输入输出格式相同，直接复制文件
        if input_format == output_format:
            output_filename = f"{name}.{output_format}"
            output_path = os.path.join(OUTPUT_DIR, output_filename)


            import shutil
            print(f"[转换策略] 输入输出格式相同，执行直接复制")
            shutil.copy(input_path, output_path)
            print(f"[完成] 直接复制文件: {output_path}")
            return True, output_path
        
        print(f"[转换策略] 确定为: {input_filename} ({input_category}) -> {output_format} ({output_category})")
        
        # 同类型转换 - 使用相应的中间格式
        if input_category == output_category:
            print(f"[转换路径] 同类型转换 ({input_category})")
            
            if input_category == 'cad':
                print(f"[转换桥梁] 将使用STEP作为中间格式")
                # 使用STEP作为中间格式
                if input_format not in ('step', 'stp'):
                    # 先转为STEP
                    step_filename = f"{name}_temp.step"
                    step_path = os.path.join(TMP_DIR, step_filename)
                    print(f"[第一步] 转换 {input_format} -> STEP: {input_filename} -> {step_filename}")
                    success, result = convert_file(input_filename, "step")
                    if not success:
                        print(f"[失败] 转换到中间格式STEP失败: {result}")
                        return False, f"转换到中间格式STEP失败: {result}"
                    
                    # 第一步成功后，result包含了输出的STEP文件路径
                    # STEP文件实际位于output目录，需要复制到temp目录
                    actual_step_path = result
                    if os.path.exists(actual_step_path):
                        # 复制到temp目录
                        import shutil
                        shutil.copy(actual_step_path, step_path)
                        print(f"[中间处理] 复制STEP文件从 {actual_step_path} 到 {step_path}")
                    else:
                        print(f"[错误] 找不到生成的STEP文件: {actual_step_path}")
                        return False, f"找不到生成的STEP文件"
                    
                    # 从STEP转为目标格式
                    print(f"[第二步] 转换 STEP -> {output_format}: {step_filename} -> output")
                    # 需要将temp目录中的STEP文件复制到input目录，以便convert_file能找到它
                    step_input_path = os.path.join(INPUT_DIR, step_filename)
                    shutil.copy(step_path, step_input_path)
                    print(f"[中间处理] STEP文件已复制到input目录: {step_input_path}")

                    # 然后使用convert_file转换
                    step_to_target_success, step_to_target_result = convert_file(step_input_path, output_format)

                    # # 清理input目录中的临时STEP文件
                    # if os.path.exists(step_input_path):
                    #     os.remove(step_input_path)
                    #     print(f"[清理] 删除input目录中的临时STEP文件: {step_input_path}")
                    
                    if step_to_target_success:
                        print(f"[成功] 通过STEP桥接完成转换: {input_format} -> STEP -> {output_format}")
                    else:
                        print(f"[失败] STEP到{output_format}转换失败: {step_to_target_result}")
                    
                    return step_to_target_success, step_to_target_result
                else:
                    # 输入已经是STEP，直接转换到目标格式
                    print(f"[简化路径] 输入已经是STEP格式，直接转换到{output_format}")
                    success, result = convert_file(input_filename, output_format)
                    if success:
                        print(f"[成功] 直接从STEP转换到{output_format}")
                    else:
                        print(f"[失败] 直接从STEP转换失败: {result}")
                    return success, result
                    
            elif input_category == 'print':
                print(f"[转换桥梁] 将使用3MF作为中间格式")
                # 使用3MF作为中间格式
                if input_format != '3mf':
                    # 先转为3MF
                    mf_filename = f"{name}_temp.3mf"
                    mf_path = os.path.join(TMP_DIR, mf_filename)
                    print(f"[第一步] 转换 {input_format} -> 3MF: {input_filename} -> {mf_filename}")
                    success, result = convert_file(input_filename, "3mf")
                    if not success:
                        print(f"[失败] 转换到中间格式3MF失败: {result}")
                        return False, f"转换到中间格式3MF失败: {result}"
                    
                    # 从3MF转为目标格式
                    print(f"[第二步] 转换 3MF -> {output_format}: {mf_filename} -> output")
                    success, result = convert_file(mf_filename, output_format)
                    # 清理临时文件
                    # if os.path.exists(mf_path):
                    #     print(f"[清理] 删除临时3MF文件: {mf_path}")
                    #     os.remove(mf_path)
                    
                    if success:
                        print(f"[成功] 通过3MF桥接完成转换: {input_format} -> 3MF -> {output_format}")
                    else:
                        print(f"[失败] 3MF到{output_format}转换失败: {result}")
                    
                    return success, result
                else:
                    # 输入已经是3MF，直接转换到目标格式
                    print(f"[简化路径] 输入已经是3MF格式，直接转换到{output_format}")
                    success, result = convert_file(input_filename, output_format)
                    if success:
                        print(f"[成功] 直接从3MF转换到{output_format}")
                    else:
                        print(f"[失败] 直接从3MF转换失败: {result}")
                    return success, result
                    
            elif input_category == 'mesh':
                print(f"[转换桥梁] 将使用OBJ作为中间格式")
                # 使用OBJ作为中间格式
                if input_format != 'obj':
                    # 先转为OBJ
                    obj_filename = f"{name}_temp.obj"
                    obj_path = os.path.join(TMP_DIR, obj_filename)
                    print(f"[第一步] 转换 {input_format} -> OBJ: {input_filename} -> {obj_filename}")
                    success, result = convert_file(input_filename, "obj")
                    if not success:
                        print(f"[失败] 转换到中间格式OBJ失败: {result}")
                        return False, f"转换到中间格式OBJ失败: {result}"
                    
                    # 从OBJ转为目标格式
                    print(f"[第二步] 转换 OBJ -> {output_format}: {obj_filename} -> output")
                    success, result = convert_file(obj_filename, output_format)
                    # 清理临时文件
                    if os.path.exists(obj_path):
                        print(f"[清理] 删除临时OBJ文件: {obj_path}")
                        os.remove(obj_path)
                    
                    if success:
                        print(f"[成功] 通过OBJ桥接完成转换: {input_format} -> OBJ -> {output_format}")
                    else:
                        print(f"[失败] OBJ到{output_format}转换失败: {result}")
                    
                    return success, result
                else:
                    # 输入已经是OBJ，直接转换到目标格式
                    print(f"[简化路径] 输入已经是OBJ格式，直接转换到{output_format}")
                    success, result = convert_file(input_filename, output_format)
                    if success:
                        print(f"[成功] 直接从OBJ转换到{output_format}")
                    else:
                        print(f"[失败] 直接从OBJ转换失败: {result}")
                    return success, result
        
        # 跨类型转换 - 可能需要多步转换
        else:
            print(f"[转换路径] 跨类型转换 ({input_category} -> {output_category})")
            
            # CAD -> 网格/打印
            if input_category == 'cad' and (output_category == 'print' or output_category == 'mesh'):
                print(f"[转换策略] CAD格式到网格/打印格式，通常使用直接转换效果较好")
                # 直接转换通常效果较好
                success, result = convert_file(input_filename, output_format)
                if success:
                    print(f"[成功] CAD直接转换到{output_category}: {input_format} -> {output_format}")
                else:
                    print(f"[失败] CAD到{output_category}转换失败: {result}")
                return success, result
                
            # 网格/打印 -> CAD (最复杂的转换路径)
            elif (input_category == 'print' or input_category == 'mesh') and output_category == 'cad':
                print(f"[转换策略] 网格/打印格式到CAD格式，这是最复杂的转换路径")
                # 对于网格到CAD的转换，可能需要先转成中间网格格式
                step_filename = f"{name}_temp.step"
                step_path = os.path.join(TMP_DIR, step_filename)
                
                # 使用FreeCAD的网格到STEP转换能力
                try:
                    print(f"[高级转换] 尝试将网格格式直接转换为STEP: {input_filename}")
                    # 导入FreeCAD模块
                    import FreeCAD
                    import Mesh
                    import Part
                    
                    # 创建新文档
                    doc = FreeCAD.newDocument("MeshConversion")
                    print(f"[FreeCAD] 创建新文档 'MeshConversion'")
                    
                    # 导入网格文件
                    print(f"[FreeCAD] 导入网格文件: {input_path}")
                    mesh_obj = Mesh.Mesh(input_path)
                    mesh_feature = doc.addObject("Mesh::Feature", "MeshObject")
                    mesh_feature.Mesh = mesh_obj
                    
                    # 尝试转换为实体（网格转CAD的关键部分）
                    print(f"[FreeCAD] 将网格转换为Shape")
                    shape = Part.Shape()
                    shape.makeShapeFromMesh(mesh_obj.Topology, 0.1)
                    
                    # 创建实体
                    print(f"[FreeCAD] 从Shape创建Solid")
                    solid = Part.makeSolid(shape)
                    solid_obj = doc.addObject("Part::Feature", "SolidObject")
                    solid_obj.Shape = solid
                    
                    # 导出为STEP
                    print(f"[FreeCAD] 导出为STEP: {step_path}")
                    Part.export([solid_obj], step_path)
                    
                    # 从STEP转换到目标CAD格式
                    print(f"[FreeCAD] 从STEP转换到目标格式: {output_format}")
                    # 需要将temp目录中的STEP文件复制到input目录，以便convert_file能找到它
                    step_input_path = os.path.join(INPUT_DIR, step_filename)  # 使用绝对路径
                    import shutil
                    try:
                        shutil.copy(step_path, step_input_path)
                        print(f"[FreeCAD] 临时STEP文件已复制到input目录: {step_input_path}")
                    except Exception as e:
                        print(f"[警告] 复制文件失败: {str(e)}")

                    # 然后使用convert_file转换
                    step_to_target_success, step_to_target_result = convert_file(step_input_path, output_format)

                    # 清理input目录中的临时STEP文件
                    if os.path.exists(step_input_path):
                        os.remove(step_input_path)
                        print(f"[清理] 删除input目录中的临时STEP文件: {step_input_path}")
                        
                    if step_to_target_success:
                        print(f"[成功] 网格重建并转换完成: {input_format} -> STEP -> {output_format}")
                        return True, step_to_target_result
                    else:
                        print(f"[失败] STEP到{output_format}转换失败: {step_to_target_result}")
                        return False, f"STEP到{output_format}转换失败: {step_to_target_result}"
                        
                except Exception as e:
                    print(f"[失败] 网格到CAD高级转换失败，错误: {str(e)}")
                    print(f"[备选方案] 尝试直接转换")
                    # 清理临时文件
                    if os.path.exists(step_path):
                        print(f"[清理] 删除临时STEP文件: {step_path}")
                        os.remove(step_path)
                    
                    # 备选方案：直接转换（有些情况下反而效果更好）
                    success, result = convert_file(input_filename, output_format)
                    if success:
                        print(f"[成功] 直接转换成功: {input_format} -> {output_format}")
                    else:
                        print(f"[失败] 直接转换失败: {result}")
                    return success, result
            
            # 网格 -> 打印 或 打印 -> 网格
            elif (input_category == 'print' and output_category == 'mesh') or (input_category == 'mesh' and output_category == 'print'):
                print(f"[转换策略] 网格与打印格式互转")
                
                # 首先尝试使用trimesh库直接转换(如果可用)
                if HAS_TRIMESH:
                    try:
                        print(f"[备选方案] 使用trimesh库直接转换 {input_format} -> {output_format}")
                        output_filename = f"{name}.{output_format}"


                        output_path = os.path.join(PROJECT_ROOT, output_filename)
                        # project = PROJECT_ROOT
                        # 使用trimesh加载并导出
                        mesh = trimesh.load(input_path)
                        mesh.export(output_path)
                        
                        if os.path.exists(output_path):
                            print(f"[成功] 使用trimesh直接转换成功: {input_format} -> {output_format}")
                            return True, output_path
                        else:
                            print(f"[警告] trimesh导出未能创建文件，尝试FreeCAD方法")
                    except Exception as te:
                        print(f"[警告] trimesh转换失败: {str(te)}，尝试FreeCAD方法")
                
                # 如果trimesh不可用或失败，回退到FreeCAD方法
                print(f"[转换] 尝试使用FreeCAD转换")
                success, result = convert_file(input_filename, output_format)
                if success:
                    print(f"[成功] FreeCAD直接转换: {input_format} -> {output_format}")
                else:
                    # 如果FreeCAD也失败，尝试通过STL桥接
                    print(f"[警告] FreeCAD直接转换失败: {result}")
                    print(f"[备选方案] 尝试通过STL桥接")
                    
                    # 先转为STL
                    stl_filename = f"{name}_temp.stl"
                    stl_path = os.path.join(TMP_DIR, stl_filename)
                    stl_success, stl_result = convert_file(input_filename, "stl")
                    
                    if not stl_success:
                        print(f"[失败] 转换到STL失败: {stl_result}")
                        return False, f"无法完成转换，所有方法都失败: {result}"
                    
                    # 从STL转为目标格式
                    print(f"[桥接] 转换 STL -> {output_format}")
                    stl_to_target_success, stl_to_target_result = convert_file(stl_filename, output_format)
                    
                    # 清理临时STL文件
                    stl_input_path = os.path.join(INPUT_DIR, stl_filename)
                    if os.path.exists(stl_input_path):
                        os.remove(stl_input_path)
                    
                    if stl_to_target_success:
                        print(f"[成功] 通过STL桥接完成转换: {input_format} -> STL -> {output_format}")
                        return True, stl_to_target_result
                    else:
                        print(f"[失败] 所有转换方法均失败")
                        return False, f"无法完成转换: {stl_to_target_result}"
                
                return success, result
        
        # 如果所有策略都失败，回退到直接转换
        print("[最终方案] 使用直接转换策略...")
        success, result = convert_file(input_filename, output_format)
        if success:
            print(f"[成功] 最终直接转换成功: {input_format} -> {output_format}")
        else:
            print(f"[失败] 最终直接转换失败: {result}")
        return success, result
        
    except Exception as e:
        error_msg = f"转换过程中发生错误: {str(e)}"
        print(f"[错误] {error_msg}")
        return False, error_msg

# 示例用法 - 可以直接调用函数而不需要命令行参数
def example_usage():
    """
    示例：如何直接在代码中调用转换函数
    """
    # 示例文件名和格式
    input_file = "test.step"
    output_format = "dxf"
    
    # 调用转换函数
    success, result = convert_file(input_file, output_format)
    
    if success:
        print(f"转换完成，输出文件路径: {result}")
    else:
        print(f"转换失败: {result}")

# 保留命令行接口以便测试
def main():
    """
    主函数，处理命令行参数并调用转换函数
    """
    if len(sys.argv) != 3:
        print("用法: python convert.py <输入文件名> <输出格式>")
        print("例如: python convert.py model.step obj")
        return
    
    input_filename = sys.argv[1]
    output_format = sys.argv[2]
    
    convert_file(input_filename, output_format)

if __name__ == "__main__":
    # 如果作为脚本运行，则使用命令行参数
    example_usage()
    # if len(sys.argv) > 1:
    #     main()
    # else:
        # 否则运行示例
