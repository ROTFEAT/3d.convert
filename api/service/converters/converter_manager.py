import os
import importlib
import logging
import pkgutil
from api.service.converters.base import BaseConverter
from collections import defaultdict, deque

class ConverterManager:
    """
    转换器管理器 - 负责动态加载和管理各种文件格式转换器
    
    这个类自动从converters和plugin目录加载所有转换器类，并根据它们支持的
    输入和输出格式进行注册。提供了获取特定转换功能的接口。
    支持通过中间格式的多步转换路由。
    """
    
    def __init__(self):
        """初始化转换器管理器并加载所有可用转换器"""
        self.registry = {}
        self.logger = logging.getLogger(__name__)
        # 格式转换图：用于路由寻径
        self.format_graph = defaultdict(list)
        self._load_converters()
        self._build_format_graph()
        self.logger.info(f"已加载 {len(self.registry)} 个转换器")
        
    def _load_converters(self):
        """从converters目录和plugin目录动态加载所有转换器"""
        # 加载 converters 目录下的转换器
        self._load_from_directory("service.converters", os.path.join(os.path.dirname(__file__), "converters"))
        
        # 加载 plugin 目录下的转换器
        plugin_path = "service.converters.plugin"
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugin")
        
        if os.path.exists(plugin_dir):
            self.logger.debug(f"从插件目录加载转换器: {plugin_dir}")
            
            # 方法1: 直接遍历目录文件
            for file in os.listdir(plugin_dir):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    self._load_module(f"{plugin_path}.{module_name}")
            
            # 方法2: 使用pkgutil遍历包中的所有模块(更强大，但需要确保plugin是一个有效的Python包)
            try:
                plugin_package = importlib.import_module(plugin_path)
                for _, name, ispkg in pkgutil.iter_modules(plugin_package.__path__, plugin_package.__name__ + '.'):
                    if not ispkg and not name.endswith('__init__'):
                        self._load_module(name)
            except Exception as e:
                self.logger.error(f"使用pkgutil加载插件模块时出错: {str(e)}")
    
    def _load_from_directory(self, package_path, directory_path):
        """从指定目录加载转换器"""
        if not os.path.exists(directory_path):
            self.logger.warning(f"转换器目录不存在: {directory_path}")
            return
            
        for file in os.listdir(directory_path):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = file[:-3]
                self._load_module(f"{package_path}.{module_name}")
    
    def _load_module(self, module_path):
        """加载指定路径的模块并注册转换器"""
        self.logger.debug(f"尝试加载模块: {module_path}")
        
        try:
            module = importlib.import_module(module_path)
            
            for item_name in dir(module):
                item = getattr(module, item_name)
                
                # 检查是否为BaseConverter的子类（但不是BaseConverter本身）
                if (isinstance(item, type) and 
                    issubclass(item, BaseConverter) and 
                    item is not BaseConverter):
                    
                    try:
                        instance = item()
                        input_fmt = instance.input_format().lower()
                        output_fmt = instance.output_format().lower()
                        key = f"{input_fmt}_to_{output_fmt}"
                        
                        self.registry[key] = instance
                        self.logger.info(f"已注册转换器: {key} ({item_name})")
                        
                    except Exception as e:
                        self.logger.error(f"实例化转换器 {item_name} 时出错: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"加载模块 {module_path} 时出错: {str(e)}")

    def _build_format_graph(self):
        """构建格式转换关系图，用于路由寻径"""
        # 清空现有图
        self.format_graph.clear()
        
        # 为每个已注册的转换器建立图的边
        for key, converter in self.registry.items():
            input_fmt = converter.input_format().lower()
            output_fmt = converter.output_format().lower()
            
            # 记录从input_fmt可以转换到output_fmt
            # 元组包含(目标格式, 转换器键名, 权重)
            # 权重根据转换的直接性调整：直接转换权重低，间接转换权重高
            # 特殊处理同名不同扩展名的格式(如step/stp, iges/igs)给予更低权重
            weight = 1
            if (input_fmt in ['step', 'stp'] and output_fmt in ['step', 'stp']) or \
               (input_fmt in ['iges', 'igs'] and output_fmt in ['iges', 'igs']):
                weight = 0.5  # 给予更低的权重以优先选择
                
            self.format_graph[input_fmt].append((output_fmt, key, weight))
            
        self.logger.debug(f"已构建格式转换图，包含 {len(self.format_graph)} 个源格式")
        
        # 打印所有可能的转换路径，便于调试
        formats = self.list_all_supported_formats()
        self.logger.debug(f"支持的格式: {formats}")
        
        # 打印图的连接情况
        for fmt, edges in self.format_graph.items():
            self.logger.debug(f"格式 {fmt} 可转换为: {', '.join([e[0] for e in edges])}")

    def find_conversion_path(self, input_fmt, output_fmt, max_steps=3):
        """
        查找从input_fmt到output_fmt的最佳转换路径
        
        参数:
            input_fmt: 输入格式
            output_fmt: 目标格式
            max_steps: 最大允许的转换步骤数
            
        返回:
            转换路径列表，每个元素是(源格式,目标格式,转换器键名)
            如果没有找到路径，返回空列表
        """
        input_fmt = input_fmt.lower()
        output_fmt = output_fmt.lower()
        
        # 格式相同时不需要转换
        if input_fmt == output_fmt:
            return []
            
        # 直接转换可用时，返回单步路径
        direct_key = f"{input_fmt}_to_{output_fmt}"
        if direct_key in self.registry:
            return [(input_fmt, output_fmt, direct_key)]
            
        # 使用Dijkstra算法查找最短路径
        import heapq
        
        # 初始化距离和前驱节点
        dist = {input_fmt: 0}
        prev = {}
        pq = [(0, input_fmt)]  # (距离, 格式)
        
        while pq:
            cost, current = heapq.heappop(pq)
            
            # 已找到目标
            if current == output_fmt:
                break
                
            # 超过最大步数
            if cost >= max_steps:
                continue
                
            # 遍历所有邻接格式
            for next_fmt, converter_key, weight in self.format_graph[current]:
                new_cost = cost + weight
                
                if next_fmt not in dist or new_cost < dist[next_fmt]:
                    dist[next_fmt] = new_cost
                    prev[next_fmt] = (current, converter_key)
                    heapq.heappush(pq, (new_cost, next_fmt))
        
        # 如果没有找到路径
        if output_fmt not in prev:
            return []
            
        # 重建路径
        path = []
        current = output_fmt
        
        while current != input_fmt:
            prev_fmt, converter_key = prev[current]
            path.append((prev_fmt, current, converter_key))
            current = prev_fmt
            
        # 反转路径（从源到目标）
        path.reverse()
        return path
        
    def convert_with_path(self, input_path, output_path, conversion_path=None, input_fmt=None, output_fmt=None, **kwargs):
        """
        使用找到的路径执行多步格式转换
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            conversion_path: 预先计算的转换路径，如果为None则根据input_fmt和output_fmt计算
            input_fmt: 输入格式（当conversion_path为None时必须提供）
            output_fmt: 输出格式（当conversion_path为None时必须提供）
            kwargs: 传递给转换器的额外参数
            
        返回:
            (bool, str): 转换是否成功，最终输出路径或错误信息
        """
        # 获取转换路径
        path = conversion_path
        if not path and input_fmt and output_fmt:
            path = self.find_conversion_path(input_fmt, output_fmt)
        
        if not path:
            error_msg = f"无法找到从 {input_fmt} 到 {output_fmt} 的转换路径"
            self.logger.error(error_msg)
            return False, error_msg
            
        self.logger.info(f"使用转换路径: {path}")
        
        # 只有一步转换时，直接使用转换器
        if len(path) == 1:
            src_fmt, dst_fmt, converter_key = path[0]
            converter = self.registry[converter_key]
            success, result_path = converter.convert(input_path, output_path, **kwargs)
            if success:
                return True, result_path
            else:
                return False, f"转换失败: {src_fmt} -> {dst_fmt}"
            
        # 多步转换，需要创建临时文件
        import tempfile
        import os
        
        temp_files = []
        current_input = input_path
        
        try:
            # 执行除最后一步外的所有转换
            for i, (src_fmt, dst_fmt, converter_key) in enumerate(path[:-1]):
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix=f'.{dst_fmt}', delete=False) as temp:
                    temp_path = temp.name
                    temp_files.append(temp_path)
                
                # 执行当前步骤的转换
                converter = self.registry[converter_key]
                success, result = converter.convert(current_input, temp_path, **kwargs)
                
                if not success:
                    error_msg = f"转换路径中的步骤 {i+1} 失败: {src_fmt} -> {dst_fmt}"
                    self.logger.error(error_msg)
                    return False, error_msg
                    
                # 更新下一步的输入
                current_input = temp_path
                self.logger.info(f"中间转换成功: {src_fmt} -> {dst_fmt}")
            
            # 执行最后一步转换
            src_fmt, dst_fmt, converter_key = path[-1]
            converter = self.registry[converter_key]
            success, result_path = converter.convert(current_input, output_path, **kwargs)
            
            if success:
                self.logger.info(f"最终转换成功: {src_fmt} -> {dst_fmt}")
                return True, result_path
            else:
                return False, f"最后一步转换失败: {src_fmt} -> {dst_fmt}"
                
        finally:
            # 清理临时文件
            for temp_path in temp_files:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as e:
                    self.logger.warning(f"清理临时文件失败: {str(e)}")
    
    def convert(self, input_path, output_path, input_fmt=None, output_fmt=None, **kwargs):
        """
        统一的转换入口，自动处理格式检测和路径查找
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            input_fmt: 输入格式，如果为None则从文件扩展名推断
            output_fmt: 输出格式，如果为None则从文件扩展名推断
            kwargs: 传递给转换器的额外参数
            
        返回:
            (bool, str): 转换是否成功，最终输出路径或错误信息
        """
        # 如果未提供格式，从文件扩展名推断
        if not input_fmt:
            input_fmt = os.path.splitext(input_path)[1].lower().lstrip('.')
        if not output_fmt:
            output_fmt = os.path.splitext(output_path)[1].lower().lstrip('.')
            
        input_fmt = input_fmt.lower()
        output_fmt = output_fmt.lower()
        
        self.logger.info(f"请求转换: {input_fmt} -> {output_fmt}, {input_path} -> {output_path}")
        
        # 格式相同时，直接复制文件
        if input_fmt == output_fmt:
            import shutil
            try:
                shutil.copy2(input_path, output_path)
                return True, output_path
            except Exception as e:
                return False, f"复制文件失败: {str(e)}"
        
        # 查找转换路径并执行转换
        path = self.find_conversion_path(input_fmt, output_fmt)
        return self.convert_with_path(input_path, output_path, path, **kwargs)
    
    def get_converter(self, input_fmt, output_fmt):
        """
        获取指定格式之间的转换器，仅返回直接转换的转换器
        
        参数:
            input_fmt: 输入文件格式 (如 'stl')
            output_fmt: 输出文件格式 (如 'obj')
            
        返回:
            对应的转换器实例，如果不存在则返回None
        """
        key = f"{input_fmt.lower()}_to_{output_fmt.lower()}"
        converter = self.registry.get(key)
        
        if not converter:
            self.logger.warning(f"未找到直接转换器: {key}")
            
        return converter
    
    def list_available_conversions(self):
        """列出所有可用的直接格式转换"""
        return list(self.registry.keys())
        
    def list_all_supported_formats(self):
        """列出所有支持的格式（作为输入或输出）"""
        formats = set()
        for key in self.registry:
            src, dst = key.split('_to_')
            formats.add(src)
            formats.add(dst)
        return sorted(list(formats))
        
    def list_possible_conversions(self, max_steps=3):
        """
        列出所有可能的格式转换，包括多步转换
        
        参数:
            max_steps: 最大转换步骤数
            
        返回:
            列表，每个元素为(输入格式, 输出格式, 步骤数, 转换路径)
        """
        formats = self.list_all_supported_formats()
        results = []
        
        for src_fmt in formats:
            for dst_fmt in formats:
                if src_fmt == dst_fmt:
                    continue
                    
                path = self.find_conversion_path(src_fmt, dst_fmt, max_steps)
                if path:
                    # 格式化转换路径为易读形式
                    path_str = " -> ".join([f"{s}->{d}" for s, d, _ in path])
                    results.append((src_fmt, dst_fmt, len(path), path_str))
                    
        return results
    
    def reload_converters(self):
        """重新加载所有转换器"""
        self.registry.clear()
        self._load_converters()
        self._build_format_graph()
        return len(self.registry)
        
    def visualize_graph(self):
        """
        生成格式转换图的可视化表示，返回DOT语言字符串
        
        需要安装graphviz库，可以通过 pip install graphviz 安装
        """
        dot_str = "digraph G {\n"
        dot_str += "  rankdir=LR;\n"  # 从左到右布局
        
        # 添加节点
        formats = self.list_all_supported_formats()
        for fmt in formats:
            dot_str += f'  "{fmt}" [shape=box, style=filled, fillcolor=lightblue];\n'
            
        # 添加边
        for src_fmt, edges in self.format_graph.items():
            for dst_fmt, key, weight in edges:
                dot_str += f'  "{src_fmt}" -> "{dst_fmt}" [label="{weight:.1f}"];\n'
                
        dot_str += "}\n"
        return dot_str
        
    def save_graph_visualization(self, output_file="format_graph.png"):
        """
        将格式转换图保存为图像文件
        
        参数:
            output_file: 输出文件路径，支持png、pdf、svg等格式
            
        返回:
            是否成功保存
        """
        try:
            import graphviz
            dot = graphviz.Source(self.visualize_graph())
            dot.render(os.path.splitext(output_file)[0], format=os.path.splitext(output_file)[1][1:], cleanup=True)
            return True
        except Exception as e:
            self.logger.error(f"生成图形可视化失败: {str(e)}")
            return False

# 测试代码
if __name__ == "__main__":
    # 配置日志
    manager = ConverterManager()
    # path = manager.find_conversion_path("step", "obj")
    # print(f"转换路径: {path}")
    # 执行转换
    success, result = manager.convert(
        input_path="C:\\Users\\13016\\Downloads\\sadas.gltf",
        output_path="C:\\Users\\13016\\Downloads\\sdas.iges",
    )
    if success:
        print(f"转换成功，输出文件: {result}")
    else:
        print(f"转换失败: {result}")

    # logging.basicConfig(level=logging.DEBUG,
    #                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #
    # # 创建转换器管理器
    # manager = ConverterManager()
    #
    # # 打印所有支持的格式
    # print("支持的格式:")
    # for fmt in manager.list_all_supported_formats():
    #     print(f" - {fmt}")
    #
    # # 打印所有可能的转换
    # print("\n可能的转换:")
    # for src, dst, steps, path in manager.list_possible_conversions():
    #     print(f" - {src} -> {dst} ({steps}步): {path}")
    #
    # # 尝试保存图可视化
    # try:
    #     if manager.save_graph_visualization("format_graph.png"):
    #         print("\n已保存格式转换图到 format_graph.png")
    # except:
    #     print("\n保存格式转换图需要安装graphviz库")
    #
    # # 示例：查找从step到obj的转换路径
    # path = manager.find_conversion_path("step", "obj")
    # if path:
    #     print(f"\n从STEP到OBJ的最短路径: {path}")
    #     print("转换路径: " + " -> ".join([f"{s}->{d}" for s, d, _ in path]))
    # else:
    #     print("\n无法找到从STEP到OBJ的转换路径")
