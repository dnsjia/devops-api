SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for rbac_menu
-- ----------------------------
DROP TABLE IF EXISTS `rbac_menu`;
CREATE TABLE `rbac_menu` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `icon` varchar(32) NOT NULL,
  `path` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sort` int(11) NOT NULL,
  `pid_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `rbac_menu_pid_id_a43b3c84_fk_rbac_menu_id` (`pid_id`),
  CONSTRAINT `rbac_menu_pid_id_a43b3c84_fk_rbac_menu_id` FOREIGN KEY (`pid_id`) REFERENCES `rbac_menu` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of rbac_menu
-- ----------------------------
INSERT INTO `rbac_menu` VALUES ('1', '资产管理', 'cloud-server', '', '1', '1', null);
INSERT INTO `rbac_menu` VALUES ('2', '服务器', '', '/cmdb/server', '1', '11', '1');
INSERT INTO `rbac_menu` VALUES ('3', '作业配置', 'control', '', '1', '2', null);
INSERT INTO `rbac_menu` VALUES ('4', '执行任务', '', '/task/execute', '1', '21', '3');
INSERT INTO `rbac_menu` VALUES ('5', '任务模版', '', '/task/template', '1', '22', '3');
INSERT INTO `rbac_menu` VALUES ('6', '容器管理', 'deployment-unit', '', '1', '3', null);
INSERT INTO `rbac_menu` VALUES ('7', '节点池', '', '/container/nodes', '1', '31', '6');
INSERT INTO `rbac_menu` VALUES ('8', '工作负载', '', '/container/workload', '1', '32', '6');
INSERT INTO `rbac_menu` VALUES ('9', '运维工具', 'coffee', '', '1', '4', null);
INSERT INTO `rbac_menu` VALUES ('10', '应用诊断', '', '/application/diagnosis', '1', '41', '9');
INSERT INTO `rbac_menu` VALUES ('11', '用户管理', 'user', '', '1', '9', null);
INSERT INTO `rbac_menu` VALUES ('12', '用户中心', '', '/user/manage', '1', '91', '11');
INSERT INTO `rbac_menu` VALUES ('13', '角色列表', '', '/user/roles', '1', '92', '11');
