-- MySQL dump 10.13  Distrib 9.4.0, for Win64 (x86_64)
--
-- Host: localhost    Database: trader_db
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `trader_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `trader_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `trader_db`;

--
-- Table structure for table `current_trades`
--

DROP TABLE IF EXISTS `current_trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `current_trades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ticket` varchar(100) NOT NULL,
  `trader_id` int NOT NULL,
  `server` varchar(100) NOT NULL,
  `symbol` varchar(50) NOT NULL,
  `side` enum('BUY','SELL') NOT NULL,
  `lot_size` decimal(10,4) NOT NULL,
  `open_price` decimal(18,8) NOT NULL,
  `stop_loss` decimal(18,8) DEFAULT NULL,
  `take_profit` decimal(18,8) DEFAULT NULL,
  `trailing_stop` decimal(10,2) DEFAULT NULL,
  `open_time` datetime NOT NULL,
  `close_time` datetime DEFAULT NULL,
  `close_price` decimal(18,8) DEFAULT NULL,
  `profit` decimal(18,4) DEFAULT NULL,
  `commission` decimal(18,4) DEFAULT NULL,
  `swap` decimal(18,4) DEFAULT NULL,
  `status` enum('OPEN','CLOSED','PENDING','REPLICATED') DEFAULT 'OPEN',
  `master_ticket` varchar(100) DEFAULT NULL,
  `is_master` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_ticket` (`ticket`,`server`),
  KEY `idx_trader_id` (`trader_id`),
  KEY `idx_server` (`server`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_status` (`status`),
  KEY `idx_open_time` (`open_time`),
  KEY `idx_master_ticket` (`master_ticket`),
  CONSTRAINT `current_trades_ibfk_1` FOREIGN KEY (`trader_id`) REFERENCES `traders` (`id`),
  CONSTRAINT `current_trades_ibfk_2` FOREIGN KEY (`server`) REFERENCES `servers_old` (`server`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `current_trades`
--

LOCK TABLES `current_trades` WRITE;
/*!40000 ALTER TABLE `current_trades` DISABLE KEYS */;
/*!40000 ALTER TABLE `current_trades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `master_orders`
--

DROP TABLE IF EXISTS `master_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `master_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trader_id` int NOT NULL,
  `ticket` bigint NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `type` enum('buy','sell') NOT NULL,
  `volume` decimal(10,2) NOT NULL,
  `price_open` decimal(18,5) NOT NULL,
  `sl` decimal(18,5) DEFAULT NULL,
  `tp` decimal(18,5) DEFAULT NULL,
  `price_close` decimal(18,5) DEFAULT NULL,
  `profit` decimal(18,2) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `opened_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `closed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_trader_id` (`trader_id`),
  CONSTRAINT `fk_master_order_trader` FOREIGN KEY (`trader_id`) REFERENCES `traders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `master_orders`
--

LOCK TABLES `master_orders` WRITE;
/*!40000 ALTER TABLE `master_orders` DISABLE KEYS */;
INSERT INTO `master_orders` VALUES (110,1,53858853117,'EURUSD','buy',1.00,1.15617,0.60000,2.00000,NULL,NULL,NULL,'2025-10-31 14:45:39',NULL),(111,1,54004084807,'USDSEK','buy',0.01,9.39854,9.10000,10.00000,NULL,NULL,NULL,'2025-11-13 19:00:56',NULL),(112,1,92433640,'XAUUSD','buy',0.01,4259.09000,0.00000,4258.76000,NULL,NULL,NULL,'2025-12-01 13:15:00',NULL),(113,1,92436955,'XAUUSD','buy',0.01,4256.82000,0.00000,0.00000,NULL,NULL,NULL,'2025-12-01 13:17:35',NULL),(114,1,92441557,'XAUUSD','buy',0.01,4254.81000,0.00000,4256.74000,NULL,NULL,NULL,'2025-12-01 13:21:26',NULL),(115,1,92442854,'XAUUSD','buy',0.01,4252.82000,0.00000,4256.74000,NULL,NULL,NULL,'2025-12-01 13:21:47',NULL);
/*!40000 ALTER TABLE `master_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `replication_log`
--

DROP TABLE IF EXISTS `replication_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `replication_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `original_trade_id` varchar(100) NOT NULL,
  `master_trade_id` int NOT NULL,
  `slave_trade_id` int DEFAULT NULL,
  `replication_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` enum('SUCCESS','FAILED','PENDING') DEFAULT 'PENDING',
  `error_message` text,
  PRIMARY KEY (`id`),
  KEY `master_trade_id` (`master_trade_id`),
  CONSTRAINT `replication_log_ibfk_1` FOREIGN KEY (`master_trade_id`) REFERENCES `trades` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `replication_log`
--

LOCK TABLES `replication_log` WRITE;
/*!40000 ALTER TABLE `replication_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `replication_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `server_mappings`
--

DROP TABLE IF EXISTS `server_mappings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `server_mappings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `master_server` varchar(50) NOT NULL,
  `slave_server` varchar(50) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_mapping` (`master_server`,`slave_server`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `server_mappings`
--

LOCK TABLES `server_mappings` WRITE;
/*!40000 ALTER TABLE `server_mappings` DISABLE KEYS */;
/*!40000 ALTER TABLE `server_mappings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servers`
--

DROP TABLE IF EXISTS `servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user` varchar(100) NOT NULL,
  `pwd` varchar(255) NOT NULL,
  `server` varchar(100) NOT NULL,
  `server_alias` varchar(100) DEFAULT NULL,
  `platform` enum('MT4','MT5') NOT NULL,
  `ip` varchar(50) NOT NULL,
  `port` int NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `path` varchar(255) DEFAULT NULL,
  `sort_order` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servers`
--

LOCK TABLES `servers` WRITE;
/*!40000 ALTER TABLE `servers` DISABLE KEYS */;
INSERT INTO `servers` VALUES (37,'10011270807','7oEg@tQl','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_TEST','MT5','127.0.0.1',8000,1,'2025-10-31 20:14:43','2026-08-11 12:46:41','C:\\MT5_1\\terminal64.exe',1),(42,'10011270807','7oEg@tQl','ICMarketsEU-Demo','MetaQuotes-DemoSLAVE','MT5','127.0.0.1',8001,1,'2025-11-05 11:49:22','2026-08-11 11:10:48','C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\MetaTrader 5.exe',3),(43,'19148641','Qpnldan1@1','VTMarkets-Live 2','VTMarkets-Live 2MASTER','MT5','127.0.0.1',8000,1,'2025-11-06 12:09:37','2026-08-11 11:10:48','C:\\Program Files\\MetaTrader 5\\terminal64.exe',4),(46,'81762765','Qpnldan1@1','MetaQuotes-Demo','FPMarketsLLC-LiveCHINA','MT5','127.0.0.1',8000,1,'2025-11-11 13:14:11','2026-08-11 11:10:42','C:\\Program Files\\MetaTrader 5\\terminal64.exe',5),(56,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_180_8000','MT5','192.168.1.180',8000,1,'2025-12-09 16:45:10','2026-08-11 11:10:42','C:\\Program Files\\MetaTrader 5 - 1\\terminal64.exe',6),(57,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_180_8001','MT5','192.168.1.180',8001,1,'2025-12-09 16:45:10','2026-08-11 11:10:35','C:\\Program Files\\MetaTrader 5 - 2\\terminal64.exe',8),(58,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_180_8002','MT5','192.168.1.180',8002,1,'2025-12-09 16:45:10','2026-08-11 11:10:35','C:\\Program Files\\MetaTrader 5 - 3\\terminal64.exe',7),(59,'102439177','K*TqSm5p','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_180_8003','MT5','192.168.1.180',8003,1,'2025-12-09 16:45:10','2026-08-11 11:10:16','C:\\Program Files\\MetaTrader 5 - 4\\terminal64.exe',9),(60,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_181_8000','MT5','192.168.1.181',8000,1,'2025-12-09 16:45:10','2026-08-11 11:10:11','C:\\Program Files\\MetaTrader 5 - 1\\terminal64.exe',10),(61,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_181_8001','MT5','192.168.1.181',8001,1,'2025-12-09 16:45:10','2026-08-11 11:10:02','C:\\Program Files\\MetaTrader 5 - 2\\terminal64.exe',11),(62,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_181_8002','MT5','192.168.1.181',8002,1,'2025-12-09 16:45:10','2026-08-11 11:10:02','C:\\Program Files\\MetaTrader 5 - 3\\terminal64.exe',12),(63,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_181_8003','MT5','192.168.1.181',8003,1,'2025-12-09 16:45:10','2026-08-11 12:46:47','C:\\Program Files\\MetaTrader 5 - 4\\terminal64.exe',14),(68,'102439177','K*TqSm5p','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_182_8000','MT5','192.168.1.182',8000,1,'2025-12-09 16:45:10','2026-08-11 12:46:47','C:\\Program Files\\MetaTrader 5 - 1\\terminal64.exe',15),(69,'102439177','K*TqSm5p','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_182_8001','MT5','192.168.1.182',8001,1,'2025-12-09 16:45:10','2026-08-11 12:46:47','C:\\Program Files\\MetaTrader 5 - 2\\terminal64.exe',16),(70,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_182_8002','MT5','192.168.1.182',8002,1,'2025-12-09 16:45:10','2026-08-11 12:46:47','C:\\Program Files\\MetaTrader 5 - 3\\terminal64.exe',17),(71,'10008241916','OmOy*zJ8','MetaQuotes-Demo','MetaQuotes-DemoSLAVE_182_8003','MT5','192.168.1.182',8003,1,'2025-12-09 16:45:10','2026-08-11 12:46:47','C:\\Program Files\\MetaTrader 5 - 4\\terminal64.exe',13),(72,'13130996','5H@JkqKX2m9GPr','ICMarketsEU-MT5-5','ICMarkets REALE LOCAL','MT5','127.0.0.1',8000,1,'2026-08-11 10:08:31','2026-08-11 15:12:38','C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\MetaTrader 5.exe',2);
/*!40000 ALTER TABLE `servers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servers_old`
--

DROP TABLE IF EXISTS `servers_old`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servers_old` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user` varchar(100) NOT NULL,
  `pwd` varchar(255) NOT NULL,
  `server` varchar(100) NOT NULL,
  `platform` enum('MT4','MT5') NOT NULL,
  `ip` varchar(50) NOT NULL,
  `port` int NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_server` (`server`),
  KEY `idx_platform` (`platform`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servers_old`
--

LOCK TABLES `servers_old` WRITE;
/*!40000 ALTER TABLE `servers_old` DISABLE KEYS */;
INSERT INTO `servers_old` VALUES (1,'trader1','password123','SERVER_A','MT5','192.168.1.100',443,1,'2025-10-17 17:52:31','2025-10-31 20:10:55','C:\\Program Files\\MetaTrader 5\\terminal.exe'),(2,'trader2','password456','SERVER_B','MT5','192.168.1.101',443,1,'2025-10-17 17:52:31','2025-10-17 17:52:31',NULL),(3,'trader3','password789','SERVER_C','MT4','192.168.1.102',443,1,'2025-10-17 17:52:31','2025-10-17 17:52:31',NULL),(4,'trader4','password000','SERVER_D','MT4','192.168.1.103',443,1,'2025-10-17 17:52:31','2025-10-17 17:52:31',NULL),(10,'5041922476','Zh@1TcKl','MetaQuotes-Demo','MT5','127.0.0.1',9000,1,'2025-10-31 20:14:43','2025-11-03 17:26:24','C:\\Program Files\\MetaTrader 5\\terminal64.exe');
/*!40000 ALTER TABLE `servers_old` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `slave_orders`
--

DROP TABLE IF EXISTS `slave_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `slave_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trader_id` int NOT NULL,
  `master_order_id` int DEFAULT NULL,
  `master_ticket` bigint DEFAULT NULL,
  `ticket` bigint NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `type` enum('buy','sell') NOT NULL,
  `volume` decimal(10,2) NOT NULL,
  `price_open` decimal(18,5) NOT NULL,
  `sl` decimal(18,5) DEFAULT NULL,
  `tp` decimal(18,5) DEFAULT NULL,
  `price_close` decimal(18,5) DEFAULT NULL,
  `profit` decimal(18,2) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `opened_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `closed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_trader_id` (`trader_id`),
  KEY `idx_master_order_id` (`master_order_id`),
  CONSTRAINT `fk_slave_order_master` FOREIGN KEY (`master_order_id`) REFERENCES `master_orders` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_slave_order_trader` FOREIGN KEY (`trader_id`) REFERENCES `traders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=307 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `slave_orders`
--

LOCK TABLES `slave_orders` WRITE;
/*!40000 ALTER TABLE `slave_orders` DISABLE KEYS */;
INSERT INTO `slave_orders` VALUES (230,11,NULL,NULL,152341011458,'GBPUSD','sell',0.10,1.33921,NULL,NULL,NULL,NULL,NULL,'2026-07-15 11:41:49',NULL),(231,1,NULL,NULL,152341011632,'USDJPY','buy',0.01,162.32200,NULL,NULL,NULL,NULL,NULL,'2026-07-15 11:41:50',NULL),(232,10,NULL,NULL,152373475894,'XAUUSD','sell',0.01,4117.70000,NULL,NULL,NULL,NULL,NULL,'2026-07-22 15:01:32',NULL),(233,10,NULL,NULL,152378241524,'XAUUSD','sell',0.01,4088.93000,NULL,NULL,NULL,NULL,NULL,'2026-07-23 12:09:37',NULL),(234,10,NULL,NULL,152378970899,'XAUUSD','sell',0.01,4075.68000,NULL,NULL,NULL,NULL,NULL,'2026-07-23 14:20:37',NULL),(235,10,NULL,NULL,152424723897,'XAUUSD','sell',0.01,4033.18000,NULL,NULL,NULL,NULL,NULL,'2026-08-03 17:13:44',NULL),(236,11,NULL,NULL,152436981727,'GBPUSD','buy',0.10,1.34733,NULL,NULL,NULL,NULL,NULL,'2026-08-05 15:30:45',NULL),(237,10,NULL,NULL,152457712155,'XAUUSD','sell',0.01,4322.59000,NULL,NULL,NULL,NULL,NULL,'2026-08-10 16:01:09',NULL),(238,10,NULL,NULL,152458548897,'XAUUSD','buy',0.01,4351.32000,NULL,NULL,NULL,NULL,NULL,'2026-08-10 17:43:12',NULL),(239,10,NULL,NULL,152458728376,'XAUUSD','buy',0.01,4359.31000,NULL,NULL,NULL,NULL,NULL,'2026-08-10 18:05:43',NULL),(240,10,NULL,NULL,1354438231,'XAUUSD','buy',0.01,4398.50000,NULL,NULL,NULL,NULL,NULL,'2026-08-11 15:13:11',NULL),(241,10,NULL,NULL,1354442685,'XAUUSD','buy',0.01,4399.32000,NULL,NULL,NULL,NULL,NULL,'2026-08-11 15:40:19',NULL),(242,10,NULL,NULL,1354457985,'XAUUSD','buy',0.01,4397.13000,NULL,NULL,NULL,NULL,NULL,'2026-08-11 17:02:03',NULL),(243,10,NULL,NULL,1354463815,'XAUUSD','sell',0.01,4375.60000,NULL,NULL,NULL,NULL,NULL,'2026-08-11 17:45:32',NULL),(244,10,NULL,NULL,1354548178,'XAUUSD','buy',0.01,4414.35000,NULL,NULL,NULL,NULL,NULL,'2026-08-12 14:32:26',NULL),(245,10,NULL,NULL,1354549679,'XAUUSD','buy',0.01,4427.23000,NULL,NULL,NULL,NULL,NULL,'2026-08-12 14:34:31',NULL),(246,10,NULL,NULL,1354550987,'XAUUSD','buy',0.01,4420.14000,NULL,NULL,NULL,NULL,NULL,'2026-08-12 14:36:37',NULL),(247,10,NULL,NULL,1354557792,'XAUUSD','buy',0.01,4431.59000,NULL,NULL,NULL,NULL,NULL,'2026-08-12 15:03:55',NULL),(248,10,NULL,NULL,1354579606,'XAUUSD','buy',0.01,4424.10000,NULL,NULL,NULL,NULL,NULL,'2026-08-12 17:15:51',NULL),(249,10,NULL,NULL,1354628534,'XAUUSD','sell',0.01,4373.68000,NULL,NULL,NULL,NULL,NULL,'2026-08-13 09:33:14',NULL),(250,10,NULL,NULL,1354650083,'XAUUSD','buy',0.01,4394.51000,NULL,NULL,NULL,NULL,NULL,'2026-08-13 15:01:52',NULL),(251,10,NULL,NULL,1354652693,'XAUUSD','sell',0.01,4384.43000,NULL,NULL,NULL,NULL,NULL,'2026-08-13 15:31:10',NULL),(252,10,NULL,NULL,1354660912,'XAUUSD','sell',0.01,4367.47000,NULL,NULL,NULL,NULL,NULL,'2026-08-13 16:11:50',NULL),(253,10,NULL,NULL,1358238441,'XAUUSD','sell',0.01,4403.82000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 15:30:38',NULL),(254,10,NULL,NULL,1358239508,'XAUUSD','sell',0.01,4397.29000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 15:35:45',NULL),(255,10,NULL,NULL,1358240914,'XAUUSD','sell',0.01,4391.63000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 15:42:51',NULL),(256,10,NULL,NULL,1358244932,'XAUUSD','sell',0.01,4397.32000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 16:03:34',NULL),(257,10,NULL,NULL,1358252109,'XAUUSD','sell',0.01,4397.20000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 16:34:52',NULL),(258,10,NULL,NULL,1358266362,'XAUUSD','sell',0.01,4398.19000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 17:52:24',NULL),(259,10,NULL,NULL,1358269007,'XAUUSD','sell',0.01,4385.88000,NULL,NULL,NULL,NULL,NULL,'2026-09-08 18:14:15',NULL),(260,10,NULL,NULL,1358355442,'XAUUSD','buy',0.01,4405.54000,NULL,NULL,NULL,NULL,NULL,'2026-09-09 15:04:37',NULL),(261,10,NULL,NULL,1358362477,'XAUUSD','buy',0.01,4430.63000,NULL,NULL,NULL,NULL,NULL,'2026-09-09 15:35:07',NULL),(262,10,NULL,NULL,1358402797,'XAUUSD','buy',0.01,4421.08000,NULL,NULL,NULL,NULL,NULL,'2026-09-09 20:13:36',NULL),(263,10,NULL,NULL,1358451750,'XAUUSD','sell',0.01,4391.73000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 11:36:01',NULL),(264,10,NULL,NULL,1358458705,'XAUUSD','sell',0.01,4384.72000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 12:43:31',NULL),(265,10,NULL,NULL,1358468419,'XAUUSD','sell',0.01,4371.26000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 14:04:33',NULL),(266,10,NULL,NULL,1358472010,'XAUUSD','sell',0.01,4363.39000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 14:26:08',NULL),(267,10,NULL,NULL,1358473562,'XAUUSD','sell',0.01,4356.33000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 14:31:12',NULL),(268,10,NULL,NULL,1358499539,'XAUUSD','sell',0.01,4361.53000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 16:13:04',NULL),(269,10,NULL,NULL,1358540334,'XAUUSD','sell',0.01,4314.66000,NULL,NULL,NULL,NULL,NULL,'2026-09-10 22:51:15',NULL),(270,10,NULL,NULL,1358542720,'XAUUSD','sell',0.01,4318.40000,NULL,NULL,NULL,NULL,NULL,'2026-09-11 00:35:48',NULL),(271,10,NULL,NULL,1358567087,'XAUUSD','buy',0.01,4338.35000,NULL,NULL,NULL,NULL,NULL,'2026-09-11 07:38:11',NULL),(272,10,NULL,NULL,1358569975,'XAUUSD','buy',0.01,4346.36000,NULL,NULL,NULL,NULL,NULL,'2026-09-11 07:59:31',NULL),(273,10,NULL,NULL,1358583369,'XAUUSD','buy',0.01,4350.09000,NULL,NULL,NULL,NULL,NULL,'2026-09-11 10:17:20',NULL),(274,10,NULL,NULL,1358584183,'XAUUSD','buy',0.01,4353.08000,NULL,NULL,NULL,NULL,NULL,'2026-09-11 10:25:24',NULL),(275,10,NULL,NULL,1358929784,'XAUUSD','buy',0.01,4345.12000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 14:52:34',NULL),(276,10,NULL,NULL,1358931767,'XAUUSD','buy',0.01,4350.44000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 15:12:02',NULL),(277,10,NULL,NULL,1358932788,'XAUUSD','buy',0.01,4356.86000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 15:17:38',NULL),(278,10,NULL,NULL,1358943773,'XAUUSD','buy',0.01,4341.83000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 16:40:00',NULL),(279,10,NULL,NULL,1358945927,'XAUUSD','buy',0.01,4350.02000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 16:55:42',NULL),(280,10,NULL,NULL,1358947476,'XAUUSD','buy',0.01,4352.66000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 17:03:14',NULL),(281,10,NULL,NULL,1358960644,'XAUUSD','buy',0.01,4351.00000,NULL,NULL,NULL,NULL,NULL,'2026-09-16 19:57:12',NULL),(282,10,NULL,NULL,1359006071,'XAUUSD','sell',0.01,4260.91000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 00:10:07',NULL),(283,10,NULL,NULL,1359025598,'XAUUSD','buy',0.01,4310.38000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 08:10:04',NULL),(284,10,NULL,NULL,1359040653,'XAUUSD','buy',0.01,4315.77000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 11:15:35',NULL),(285,10,NULL,NULL,1359045516,'XAUUSD','buy',0.01,4313.79000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 12:25:21',NULL),(286,10,NULL,NULL,1359057024,'XAUUSD','buy',0.01,4352.39000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 14:10:54',NULL),(287,10,NULL,NULL,1359060205,'XAUUSD','buy',0.01,4370.36000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 14:25:58',NULL),(288,10,NULL,NULL,1359076533,'XAUUSD','buy',0.01,4376.15000,NULL,NULL,NULL,NULL,NULL,'2026-09-17 16:08:47',NULL),(289,10,NULL,NULL,1359372047,'XAUUSD','buy',0.01,4335.32000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 12:01:53',NULL),(290,10,NULL,NULL,1359375086,'XAUUSD','sell',0.01,4328.52000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 12:34:52',NULL),(291,10,NULL,NULL,1359391336,'XAUUSD','buy',0.01,4341.41000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 15:15:10',NULL),(292,10,NULL,NULL,1359393511,'XAUUSD','sell',0.01,4335.66000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 15:34:36',NULL),(293,10,NULL,NULL,1359396906,'XAUUSD','buy',0.01,4339.37000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 15:50:42',NULL),(294,10,NULL,NULL,1359404847,'XAUUSD','sell',0.01,4325.11000,NULL,NULL,NULL,NULL,NULL,'2026-09-22 16:39:48',NULL),(295,10,NULL,NULL,1359469267,'XAUUSD','sell',0.01,4318.91000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 10:35:10',NULL),(296,10,NULL,NULL,1359491544,'XAUUSD','sell',0.01,4305.36000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 14:44:06',NULL),(297,10,NULL,NULL,1359494400,'XAUUSD','sell',0.01,4302.32000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 15:09:40',NULL),(298,10,NULL,NULL,1359500903,'XAUUSD','sell',0.01,4285.52000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 15:45:20',NULL),(299,10,NULL,NULL,1359508448,'XAUUSD','sell',0.01,4279.77000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 16:18:58',NULL),(300,10,NULL,NULL,1359519817,'XAUUSD','sell',0.01,4284.23000,NULL,NULL,NULL,NULL,NULL,'2026-09-23 17:36:24',NULL),(301,10,NULL,NULL,1359560503,'XAUUSD','sell',0.01,4285.01000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 07:39:27',NULL),(302,10,NULL,NULL,1359579501,'XAUUSD','sell',0.01,4263.50000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 11:02:24',NULL),(303,10,NULL,NULL,1359582504,'XAUUSD','sell',0.01,4258.65000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 11:31:52',NULL),(304,10,NULL,NULL,1359585879,'XAUUSD','sell',0.01,4252.25000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 12:06:35',NULL),(305,10,NULL,NULL,1359592993,'XAUUSD','sell',0.01,4255.96000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 13:10:20',NULL),(306,10,NULL,NULL,1359602472,'XAUUSD','buy',0.01,4282.65000,NULL,NULL,NULL,NULL,NULL,'2026-09-24 15:01:04',NULL);
/*!40000 ALTER TABLE `slave_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `symbols_mapping`
--

DROP TABLE IF EXISTS `symbols_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `symbols_mapping` (
  `id` int NOT NULL AUTO_INCREMENT,
  `master_symbol` varchar(50) NOT NULL,
  `slave_symbol` varchar(50) NOT NULL,
  `master_server` varchar(100) NOT NULL,
  `slave_server` varchar(100) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_mapping` (`master_symbol`,`slave_symbol`,`master_server`,`slave_server`),
  KEY `idx_master_symbol` (`master_symbol`),
  KEY `idx_slave_symbol` (`slave_symbol`),
  KEY `master_server` (`master_server`),
  KEY `slave_server` (`slave_server`),
  CONSTRAINT `symbols_mapping_ibfk_1` FOREIGN KEY (`master_server`) REFERENCES `servers_old` (`server`),
  CONSTRAINT `symbols_mapping_ibfk_2` FOREIGN KEY (`slave_server`) REFERENCES `servers_old` (`server`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `symbols_mapping`
--

LOCK TABLES `symbols_mapping` WRITE;
/*!40000 ALTER TABLE `symbols_mapping` DISABLE KEYS */;
INSERT INTO `symbols_mapping` VALUES (1,'EURUSD','EURUSD','SERVER_A','SERVER_B',1,'2025-10-17 17:52:31','2025-10-17 17:52:31'),(2,'GBPUSD','GBPUSD','SERVER_A','SERVER_B',1,'2025-10-17 17:52:31','2025-10-17 17:52:31'),(3,'XAUUSD','GOLD','SERVER_C','SERVER_D',1,'2025-10-17 17:52:31','2025-10-17 17:52:31'),(4,'BTCUSD','BITCOIN','SERVER_C','SERVER_D',1,'2025-10-17 17:52:31','2025-10-17 17:52:31');
/*!40000 ALTER TABLE `symbols_mapping` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `traders`
--

DROP TABLE IF EXISTS `traders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `sl` decimal(10,2) DEFAULT NULL,
  `tp` decimal(10,2) DEFAULT NULL,
  `tsl` decimal(10,2) DEFAULT NULL,
  `moltiplicatore` decimal(10,4) DEFAULT '1.0000',
  `fix_lot` decimal(10,4) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `master_server_id` int DEFAULT NULL,
  `slave_server_id` int DEFAULT NULL,
  `selected_signal` varchar(50) DEFAULT NULL,
  `custom_signal_interval` int DEFAULT NULL,
  `selected_symbol` varchar(20) DEFAULT NULL,
  `copy_interval` int DEFAULT NULL,
  `sessions_filter` varchar(255) DEFAULT 'ASIA,LONDON,NY-LON,NY,OFF',
  PRIMARY KEY (`id`),
  KEY `idx_is_active` (`is_active`),
  KEY `fk_master_server_2` (`master_server_id`),
  KEY `fk_slave_server_2` (`slave_server_id`),
  CONSTRAINT `fk_master_server_2` FOREIGN KEY (`master_server_id`) REFERENCES `servers` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_slave_server_2` FOREIGN KEY (`slave_server_id`) REFERENCES `servers` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `traders`
--

LOCK TABLES `traders` WRITE;
/*!40000 ALTER TABLE `traders` DISABLE KEYS */;
INSERT INTO `traders` VALUES (1,'Trader_Alphaa',300.00,1500.00,21.00,5.0000,0.0100,1,'2025-10-17 17:52:31','2026-08-05 11:51:47',43,37,'SUPER_LIVE',60,'XAUUSD',NULL,'ASIA,LONDON,NY-LON,NY,OFF'),(10,'Trader_Test3',300.00,1500.00,22.00,5.0000,0.0100,1,'2026-01-21 11:08:31','2026-09-24 16:21:16',43,72,'SUPER',60,'XAUUSD',NULL,'ASIA,LONDON,NY-LON,NY,OFF'),(11,'Trader_Test4',800.00,1000.00,300.00,5.0000,0.1000,1,'2026-01-21 11:09:29','2026-08-05 12:27:34',43,37,'SUPER',60,'GBPUSD',NULL,'ASIA,LONDON,NY-LON,NY,OFF');
/*!40000 ALTER TABLE `traders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trades`
--

DROP TABLE IF EXISTS `trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trade_id` varchar(100) NOT NULL,
  `server_id` varchar(50) NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `side` enum('BUY','SELL') NOT NULL,
  `quantity` decimal(18,8) NOT NULL,
  `price` decimal(18,8) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('PENDING','EXECUTED','REPLICATED') DEFAULT 'PENDING',
  PRIMARY KEY (`id`),
  UNIQUE KEY `trade_id` (`trade_id`),
  KEY `idx_server_id` (`server_id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trades`
--

LOCK TABLES `trades` WRITE;
/*!40000 ALTER TABLE `trades` DISABLE KEYS */;
/*!40000 ALTER TABLE `trades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `last_login` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('179cccdb-7482-4f1c-a891-3400d17b0d35','roberto','$2b$12$.coRCvBBygoZdVgs5S48vecI3B43b4sjCj5WCbPhAmLYDWP4oV.w.','2025-10-20 12:28:39','2025-10-30 16:43:06'),('e2e276bf-7f10-4408-94ed-15f90df68a3e','william','$2b$12$acMld1U6P8fVMNs3b6CDPuthe0L30SW4IsiR6/JZW.lcxv7v/EL6C','2025-10-20 12:27:32','2026-07-13 14:39:20');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'trader_db'
--

--
-- Dumping routines for database 'trader_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-28 15:10:41
