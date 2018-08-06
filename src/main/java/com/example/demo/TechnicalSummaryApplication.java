package com.example.demo;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.cloud.client.SpringCloudApplication;

@SpringCloudApplication
@MapperScan("com.example.demo.mapper")
public class TechnicalSummaryApplication {

	public static void main(String[] args) {
		SpringApplication.run(TechnicalSummaryApplication.class, args);
	}
}
