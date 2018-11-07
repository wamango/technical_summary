package com.example.demo;

import com.alibaba.fastjson.support.spring.GenericFastJsonRedisSerializer;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.cloud.client.SpringCloudApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.client.RestTemplate;

@EnableRetry
@SpringCloudApplication
@MapperScan("com.example.demo.mapper")
@EnableScheduling
public class TechnicalSummaryApplication {

	@Bean
	public RestTemplate restTemplate(){
		return new RestTemplate();
	}
	/**
	 * 初始化RedisTemplate
	 * @param redisConnectionFactory
	 * @return
	 */
	@Bean
	public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory redisConnectionFactory){
		RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
		redisTemplate.setConnectionFactory(redisConnectionFactory);

		//设置key和value序列方法
		redisTemplate.setKeySerializer(new StringRedisSerializer());
		redisTemplate.setValueSerializer(new GenericFastJsonRedisSerializer());
		//设置key和value序列方法
		redisTemplate.setHashKeySerializer(new StringRedisSerializer());
		redisTemplate.setHashValueSerializer(new GenericFastJsonRedisSerializer());
		redisTemplate.afterPropertiesSet();
		return redisTemplate;
	}

	public static void main(String[] args) {
		SpringApplication.run(TechnicalSummaryApplication.class, args);
	}
}
