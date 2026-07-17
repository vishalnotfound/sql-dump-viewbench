-- Sample SQL Dump
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'active',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` VALUES 
(1,'John','Doe','john@example.com','active','2024-01-01 10:00:00'),
(2,'Jane','Smith','jane@example.com','active','2024-01-02 14:30:00'),
(3,'Bob','Johnson','bob@example.com','inactive','2024-01-03 09:15:00'),
(4,'Alice','Williams','alice@example.com','active','2024-01-04 16:45:00'),
(5,'Charlie','Brown','charlie@example.com','pending','2024-01-05 11:20:00');

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `stock` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `products` VALUES 
(1,'Laptop',999.99,50),
(2,'Mouse',19.99,200),
(3,'Keyboard',49.99,150),
(4,'Monitor',299.99,75);
