/*
Navicat MySQL Data Transfer

Source Server         : 96-master
Source Server Version : 50648
Source Host           : 192.168.1.96:3306
Source Database       : ops_test

Target Server Type    : MYSQL
Target Server Version : 50648
File Encoding         : 65001

Date: 2021-06-07 13:33:55
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for rbac_permission
-- ----------------------------
DROP TABLE IF EXISTS `rbac_permission`;
CREATE TABLE `rbac_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `path` varchar(128) NOT NULL,
  `method` varchar(16) NOT NULL,
  `pid_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `rbac_permission_pid_id_6939354d_fk_rbac_permission_id` (`pid_id`),
  CONSTRAINT `rbac_permission_pid_id_6939354d_fk_rbac_permission_id` FOREIGN KEY (`pid_id`) REFERENCES `rbac_permission` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of rbac_permission
-- ----------------------------
INSERT INTO `rbac_permission` VALUES ('1', '菜单', '/api/rbac/menu/tree/', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('2', '资产管理', '', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('3', '查看服务器列表', '/api/cmdb/(?P<version>[v1|v2]+)/server', 'GET', '2');
INSERT INTO `rbac_permission` VALUES ('4', '查看服务器详情', '/api/cmdb/(?P<version>[v1|v2]+)/server/(?P<pk>\\w+.*)$', 'GET', '2');
INSERT INTO `rbac_permission` VALUES ('5', '作业配置', '', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('6', '查看执行任务列表', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/tasks/list$', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('7', '查看文件分发列表', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/send_list$', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('8', '获取执行命令机器列表', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/server$', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('9', '获取执行命令模板列表', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/template/list$', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('10', '文件分发上传接口', '/api/cmdb/v1/uploads', 'POST', '5');
INSERT INTO `rbac_permission` VALUES ('11', '执行命令下发', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/execute$', 'POST', '5');
INSERT INTO `rbac_permission` VALUES ('12', '查看命令执行详情', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/tasks/list$', 'POST', '5');
INSERT INTO `rbac_permission` VALUES ('13', '执行文件分发命令', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/sendfile$', 'POST', '5');
INSERT INTO `rbac_permission` VALUES ('14', '创建任务执行模板', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/template/list$', 'POST', '5');
INSERT INTO `rbac_permission` VALUES ('15', '命令执行结果搜索', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/execute/search', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('16', '文件分发结果搜索', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/sendfile/search', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('17', '任务执行模板搜索', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/template/search', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('18', '删除任务执行模板', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/template/list', 'DELETE', '5');
INSERT INTO `rbac_permission` VALUES ('19', '容器管理', '', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('20', '执行命令主机搜索', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/searchHost$', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('21', '读取任务执行模板内容', '/api/cmdb/(?P<version>[v1|v2]+)/ansible/template/read', 'GET', '5');
INSERT INTO `rbac_permission` VALUES ('22', '获取节点池', '/api/k8s/(?P<version>[v1|v2]+)/nodes$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('23', '查看Node节点详情', '/api/k8s/(?P<version>[v1|v2]+)/detail/node', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('24', '获取Node事件信息', '/api/k8s/v1/events/node', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('25', '计算Node节点Pod数量', '/api/k8s/(?P<version>[v1|v2]+)/pods/node$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('26', '查看监控指标', '/api/k8s/(?P<version>[v1|v2]+)/metrics/node$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('27', '查看Pod详情', '/api/k8s/(?P<version>[v1|v2]+)/pod$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('28', '获取Pod事件信息', '/api/k8s/(?P<version>[v1|v2]+)/event/pod$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('29', '编辑Pod Yaml文件', '/api/k8s/(?P<version>[v1|v2]+)/pod$', 'PUT', '19');
INSERT INTO `rbac_permission` VALUES ('30', '查看Pod日志', '/api/k8s/(?P<version>[v1|v2]+)/logs$', 'POST', '19');
INSERT INTO `rbac_permission` VALUES ('31', '删除Pod', '/api/k8s/(?P<version>[v1|v2]+)/pod$', 'DELETE', '19');
INSERT INTO `rbac_permission` VALUES ('32', '设置Node不可调度', '/api/k8s/(?P<version>[v1|v2]+)/nodes$', 'PUT', '19');
INSERT INTO `rbac_permission` VALUES ('33', '设置Node节点排水', '/api/k8s/(?P<version>[v1|v2]+)/drain/nodes$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('34', '移除Node节点', '/api/k8s/(?P<version>[v1|v2]+)/nodes$', 'DELETE', '19');
INSERT INTO `rbac_permission` VALUES ('35', '获取无状态应用列表', '/api/k8s/(?P<version>[v1|v2]+)/deployments$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('36', '获取命名空间', '/api/k8s/(?P<version>[v1|v2]+)/namespaces$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('37', '获取容器组', '/api/k8s/(?P<version>[v1|v2]+)/pods/list$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('38', '修改个人密码', '/api/account/(?P<version>[v1|v2]+)/user/password/change$', 'POST', '39');
INSERT INTO `rbac_permission` VALUES ('39', '用户管理', '', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('40', '查看用户中心', '/api/account/(?P<version>[v1|v2]+)/users$', 'GET', '39');
INSERT INTO `rbac_permission` VALUES ('41', '查看用户角色', '/api/rbac/roles/', 'GET', '39');
INSERT INTO `rbac_permission` VALUES ('42', '修改用户角色', '/api/account/(?P<version>[v1|v2]+)/user/role$', 'PUT', '39');
INSERT INTO `rbac_permission` VALUES ('43', '禁用用户', '/api/account/(?P<version>[v1|v2]+)/users$', 'PUT', '39');
INSERT INTO `rbac_permission` VALUES ('44', '删除用户', '/api/account/(?P<version>[v1|v2]+)/users$', 'DELETE', '39');
INSERT INTO `rbac_permission` VALUES ('45', '添加角色', '/api/rbac/roles/', 'POST', '39');
INSERT INTO `rbac_permission` VALUES ('46', '修改角色', '/api/rbac/roles/(.*)', 'PUT', '39');
INSERT INTO `rbac_permission` VALUES ('47', '删除角色', '/api/rbac/roles/(.*)', 'DELETE', '39');
INSERT INTO `rbac_permission` VALUES ('48', '应用诊断', '', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('49', '查看线程清单', '/api/application/(?P<version>[v1|v2]+)/diagnosis', 'POST', '48');
INSERT INTO `rbac_permission` VALUES ('50', '查看首页仪表盘统计数据', '/api/cmdb/(?P<version>[v1|v2]+)/dashboard/count$', 'GET', null);
INSERT INTO `rbac_permission` VALUES ('51', '查看诊断服务', '/api/application/v1/diagnosis/service/list', 'GET', '48');
INSERT INTO `rbac_permission` VALUES ('52', 'Deployment扩缩容', '/api/k8s/(?P<version>[v1|v2]+)/deployment/scale$', 'POST', '19');
INSERT INTO `rbac_permission` VALUES ('53', '查看Deployment详情', '/api/k8s/(?P<version>[v1|v2]+)/deployment/detail$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('54', '获取Deployment历史版本', '/api/k8s/(?P<version>[v1|v2]+)/deployment/history$', 'GET', '19');
INSERT INTO `rbac_permission` VALUES ('55', '创建Deployment回滚', '/api/k8s/(?P<version>[v1|v2]+)/deployment/history$', 'POST', '19');
INSERT INTO `rbac_permission` VALUES ('56', '查看Deployment事件', '/api/k8s/(?P<version>[v1|v2]+)/event/deployment$', 'GET', '19');
