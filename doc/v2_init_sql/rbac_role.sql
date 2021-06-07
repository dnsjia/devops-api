/*
Navicat MySQL Data Transfer

Source Server         : 96-master
Source Server Version : 50648
Source Host           : 192.168.1.96:3306
Source Database       : ops_test

Target Server Type    : MYSQL
Target Server Version : 50648
File Encoding         : 65001

Date: 2021-06-07 13:34:04
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for rbac_role
-- ----------------------------
DROP TABLE IF EXISTS `rbac_role`;
CREATE TABLE `rbac_role` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `desc` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of rbac_role
-- ----------------------------
INSERT INTO `rbac_role` VALUES ('1', 'ops', '管理员');
INSERT INTO `rbac_role` VALUES ('2', 'develop', '开发人员');
INSERT INTO `rbac_role` VALUES ('3', 'test', '测试人员');
