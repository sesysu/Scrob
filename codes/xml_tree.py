from tree_node import TreeNode

from codes.utility import delete_num_in_str


class XmlTree(object):
    """
    xml树 存储结点信息
    """

    def __init__(self, root_node):
        self.nodes = []  # 按照dfs搜集的节点 顺序为深度优先搜索
        self.root_node = root_node
        self.id = -1
        self.layers = {}  # 层次 用于搜集每一层的叶子节点
        self.clusters = {}  # 聚类
        self.clusters_id = 1  # 聚类的id从1开始
        self.leaf_nodes = []
        self.branch_nodes = []

        # 以下变量用于统计叶子各个属性的数量 用于构造xpath
        self.leaf_resource_id_count = {}
        self.leaf_text_count = {}
        self.leaf_content_count = {}

        # 用于统计分支节点的各个属性的数量 用于构造xpath
        self.branch_resource_id_count = {}
        self.branch_text_count = {}
        self.branch_content_count = {}

    def dfs(self, node, parent):
        """
        深度优先 搜集节点
        """
        # 排除系统UI
        if 'package' in node.attrib and node.attrib['package'] == 'com.android.systemui':
            return

        node.parent = parent

        node.idx = self.id
        node.get_size()
        self.nodes.append(node)
        self.id += 1

        if node.layer not in self.layers:
            self.layers[node.layer] = [node.idx]
        else:
            self.layers[node.layer].append(node.idx)

        children_xml_node = node.xml_node.getchildren()

        if len(children_xml_node) == 0:
            return

        # 记录结点的class_index 用于之后构造full_xpath使用
        class_count = {}
        # 构造子节点
        for xml_node in children_xml_node:
            child_node = TreeNode(xml_node, node.layer + 1)
            class_name = child_node.attrib['class']

            if class_name not in class_count.keys():
                class_count[class_name] = 1
                child_node.class_index = 1
                class_count[class_name] += 1
            else:
                child_node.class_index = class_count[class_name]
                class_count[class_name] += 1

            node.children.append(child_node)

        for child_node in node.children:
            self.dfs(child_node, node)

    def get_nodes_full_xpath(self, node):
        """
        构造节点的full_xpath
        """
        if node.parent is None:
            return "//"

        class_name = node.attrib['class']
        xpath_class_index = class_name + "[" + str(node.class_index) + "]"

        # 获得父节点xpath
        parent_node = node.parent

        parent_full_xpath = parent_node.full_xpath

        if parent_node.full_xpath == '':
            parent_full_xpath = self.get_nodes_full_xpath(parent_node)

        if parent_full_xpath != '//':
            full_xpath = parent_full_xpath + '/' + xpath_class_index
            node.full_xpath = full_xpath
            return full_xpath

        else:
            full_xpath = parent_full_xpath + xpath_class_index
            node.full_xpath = full_xpath
            return full_xpath

    def get_nodes_stat(self):
        """
        统计节点属性的数目 叶子节点与叶间节点分开统计
        """
        # 叶子节点 resource-id text content-desc
        for node in self.leaf_nodes:
            resource_id = node.attrib['resource-id']
            text = node.attrib['text']
            content = node.attrib['content-desc']

            if resource_id not in self.leaf_resource_id_count:
                self.leaf_resource_id_count[resource_id] = 1
            else:
                self.leaf_resource_id_count[resource_id] += 1

            if text not in self.leaf_text_count:
                self.leaf_text_count[text] = 1
            else:
                self.leaf_text_count[text] += 1

            if content not in self.leaf_content_count:
                self.leaf_content_count[content] = 1
            else:
                self.leaf_content_count[content] += 1

        # 分支节点 resource-id text content-desc
        for node in self.branch_nodes:
            resource_id = node.attrib['resource-id']
            text = node.attrib['text']
            content = node.attrib['content-desc']

            if resource_id not in self.branch_resource_id_count:
                self.branch_resource_id_count[resource_id] = 1
            else:
                self.branch_resource_id_count[resource_id] += 1

            if text not in self.branch_text_count:
                self.branch_text_count[text] = 1
            else:
                self.branch_text_count[text] += 1

            if content not in self.branch_content_count:
                self.branch_content_count[content] = 1
            else:
                self.branch_content_count[content] += 1

    def get_leaf_nodes_xpath(self):
        """
        构造叶子节点的xpath用于定位
        """

        for node in self.leaf_nodes:
            class_name = node.attrib['class']
            resource_id = node.attrib['resource-id']
            text = node.attrib['text']
            content = node.attrib['content-desc']

            if resource_id in self.leaf_resource_id_count and self.leaf_resource_id_count[resource_id] == 1:
                xpath = '//' + class_name + '[' + '@resource-id=' + '"' + resource_id + '"' + ']'
                node.xpath.append(xpath)

            if text in self.leaf_text_count and self.leaf_text_count[text] == 1:
                xpath = '//' + class_name + '[' + '@text=' + '"' + text + '"' + ']'
                node.xpath.append(xpath)

            if content in self.leaf_content_count and self.leaf_content_count[content] == 1:
                xpath = '//' + class_name + '[' + '@content=' + '"' + text + '"' + ']'
                node.xpath.append(xpath)

            id_text_count = 0
            id_content_count = 0
            text_content_count = 0
            id_text_content_count = 0

            for tmp_node in self.leaf_nodes:
                if tmp_node.attrib['resource-id'] == resource_id and \
                        tmp_node.attrib['text'] == text:
                    id_text_count += 1

                if tmp_node.attrib['resource-id'] == resource_id and \
                        tmp_node.attrib['content-desc'] == content:
                    id_content_count += 1

                if tmp_node.attrib['text'] == text and \
                        tmp_node.attrib['content-desc'] == content:
                    text_content_count += 1

                if tmp_node.attrib['resource-id'] == resource_id and \
                        tmp_node.attrib['text'] == text and \
                        tmp_node.attrib['content-desc'] == content:
                    id_text_content_count += 1

            if id_text_count == 1:
                xpath = ('//' + class_name + '[' +
                         '@resource-id=' + '"' + resource_id + '"' +
                         '&&' + '@text=' + '"' + text + '"' + ']')
                node.xpath.append(xpath)

            if id_content_count == 1:
                xpath = ('//' + class_name + '[' +
                         '@resource-id=' + '"' + resource_id + '"' +
                         '&&' + '@content-desc=' + '"' + content + '"' + ']')
                node.xpath.append(xpath)

            if text_content_count == 1:
                xpath = ('//' + class_name + '[' +
                         '@text=' + '"' + text + '"' +
                         '&&' + '@content-desc=' + '"' + content + '"' + ']')
                node.xpath.append(xpath)

            if id_text_content_count == 1:
                xpath = ('//' + class_name + '[' +
                         '@resource-id=' + '"' + resource_id + '"' +
                         '&&' + '@text=' + '"' + text + '"' +
                         '&&' + '@content-desc=' + '"' + content + '"' + ']')
                node.xpath.append(xpath)

            # 如果全部不满足 那就等于full_xpath
            # node.xpath = node.full_xpath
            node.xpath.append(node.full_xpath)

    def get_nodes(self):
        self.dfs(self.root_node, None)

        for node in self.nodes:
            self.get_nodes_full_xpath(node)
            node.get_descendants(node)
            if not node.children:
                self.leaf_nodes.append(node)
            else:
                self.branch_nodes.append(node)

        # 除去第一个根节点
        self.branch_nodes = self.branch_nodes[1:]

        for node in self.nodes[1:]:
            # 去除字符串的空格
            node.attrib['text'] = node.attrib['text'].replace(' ', '')
            node.attrib['content-desc'] = node.attrib['content-desc'].replace(' ', '')

        self.get_nodes_stat()
        self.get_leaf_nodes_xpath()

        self.nodes = self.nodes[1:]  # 第一个根节点无实际含义

        return self.nodes

    def get_clusters_from_top_down(self):
        """
        自顶向下获取元素聚类
        """
        for level in self.layers:
            nodes_idx = self.layers[level]

            for i in range(len(nodes_idx)):
                for j in range(i + 1, len(nodes_idx)):
                    x_node_idx = nodes_idx[i]
                    y_node_idx = nodes_idx[j]

                    x_node = self.nodes[x_node_idx]
                    y_node = self.nodes[y_node_idx]

                    sim = self.get_nodes_similar_score(x_node, y_node)
                    if sim >= 0.8:
                        # x_node已经属于某个聚类
                        if x_node.cluster_id != -1:
                            if y_node.idx not in self.clusters[x_node.cluster_id]:
                                self.clusters[x_node.cluster_id].append(y_node_idx)
                            y_node.cluster_id = x_node.cluster_id
                        # y_node 已经属于某个聚类
                        elif y_node.cluster_id != -1:
                            if x_node.idx not in self.clusters[y_node.cluster_id]:
                                self.clusters[y_node.cluster_id].append(x_node.idx)
                            x_node.cluster_id = y_node.cluster_id
                        # x_node 和 y_node 暂时都不属于任何聚类
                        else:
                            self.clusters[self.clusters_id] = []
                            self.clusters[self.clusters_id].append(x_node.idx)
                            self.clusters[self.clusters_id].append(y_node.idx)
                            x_node.cluster_id = self.clusters_id
                            y_node.cluster_id = self.clusters_id
                            self.clusters_id += 1

    def get_nodes_similar_score(self, x_node, y_node):
        """
        在同层次聚类的过程中判断两个叶子节点是否相似
        """
        x_node_id = x_node.attrib['resource-id']
        y_node_id = y_node.attrib['resource-id']

        flag = False
        id_sim = 0

        if len(x_node_id) == 0 or len(y_node_id) == 0:
            flag = True

        if x_node_id.find('/') != -1:
            x_node_id = x_node_id.split('/')[1]

        if y_node_id.find('/') != -1:
            y_node_id = y_node_id.split('/')[1]

        if delete_num_in_str(x_node_id) == delete_num_in_str(y_node_id) and not flag:
            return 1

        if x_node.width == y_node.width or x_node.height == y_node.height:
            return (0.8 + id_sim) / 2
        else:
            return 0
