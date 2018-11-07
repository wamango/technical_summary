package com.example.demo.cache;


import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Date;
import java.util.concurrent.TimeUnit;


/**
 * 
 * Redis操作组件类
 * 
 * @author dancy
 * @date 2015年4月01日
 * @version 1.0
 * @copyright ZCSmart Co.,Ltd.copyright 2015
 */
@Component
public class RedisTools {
    @Value("${redis.prefix}")
    private  String keyPrefix;
    @Resource
    private RedisTemplate<String,Object> redisTemplate;


    public RedisTemplate<String, Object> getRedisTemplate() {
        return redisTemplate;
    }

    public void setRedisTemplate(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }


    /**
     * 增加或更新一条hashmap数据
     * @param key 缓存的key
     * @param hKey hashmap数据的key
     * @param value hashmap数据的value
     * @param interval 缓存存在时间
     * @param unit 时间单位
     */
    public void hset(String key,String hKey,Object value,Integer interval,TimeUnit unit){
        redisTemplate.opsForHash().put(keyPrefix+key,hKey,value);
        redisTemplate.boundHashOps(keyPrefix+key).expire(interval,unit);
    }

    /**
     * 增加或更新一条hashmap数据
     * @param key 缓存的key
     * @param hKey hashmap数据的key
     * @param value hashmap数据的value
     */
    public void hset(String key,String hKey,Object value){
        redisTemplate.opsForHash().put(keyPrefix+key,hKey,value);
    }

    /**
     * 重新设置缓存失效时间
     * @param key 缓存的key
     * @param interval 失效时间
     * @param unit 时间单位
     * @return 是否设置成功
     */
    public Boolean expire(String key, Integer interval, TimeUnit unit){
        return redisTemplate.expire(keyPrefix+key,interval,unit);
    }

    /**
     * 重新设置缓存失效时间
     * @param key 缓存的key
     * @param time 失效的时刻
     * @return 是否设置成功
     */
    public Boolean expireAt(String key,Date time){
        return redisTemplate.expireAt(keyPrefix+ key,time);
    }

    /**
     * 获取缓存剩余时间
     * @param key 缓存的key
     * @param unit 时间单位
     * @return 缓存剩余时间
     */
    public long getExpire(String key,TimeUnit unit){
        return redisTemplate.getExpire(keyPrefix+key,unit);
    }

    /**
     * 获取缓存剩余时间
     * @param key 缓存的key
     * @return 缓存剩余时间（单位毫秒）
     */
    public long getExpire(String key){
        return redisTemplate.getExpire(keyPrefix+key,TimeUnit.MILLISECONDS);
    }
    
    
    /**
     * 查询hashmap中的值
     * @param key 缓存的key
     * @param hKey hashmap数据的key
     * @return hashmap数据的value，如果不存在返回null
     */
    public Object hget(String key,String hKey){
        redisTemplate.watch(keyPrefix+key);
        return redisTemplate.boundHashOps(keyPrefix+key).get(hKey);
    }

    /**
     * 通过大key获取hashMap
     * @param key 缓存的key
     * @return
     */
    public Object getMap(String key){
        redisTemplate.watch(keyPrefix+key);
        return redisTemplate.boundHashOps(keyPrefix+key).entries();
    }

    /**
     * 存储或更新缓存
     * @param key 缓存的key
     * @param value 缓存值
     * @param interval 失效时间
     * @param unit 时间单位
     */
    public void set(String key,Object value,Integer interval,TimeUnit unit){
        redisTemplate.opsForValue().set(keyPrefix+key,value,interval,unit);
    }
    
    /**
     * 存储或更新缓存
     * @param key 缓存的key
     * @param value 缓存值
     * @param offset 该方法是用 value 参数覆写(overwrite)给定 key 所储存的字符串值，从偏移量 offset 开始
     */
    public void set(String key,Object value,long offset){
        redisTemplate.opsForValue().set(key, value, offset);
    }

    /**
     * 存储或更新缓存
     * @param key 缓存的key
     * @param value 缓存值
     */
    public void set(String key,Object value){
        redisTemplate.opsForValue().set(keyPrefix+key,value);
    }

    /**
     * 获取缓存值
     * @param key 缓存的key
     * @return 缓存值
     */
    public Object get(String key){
        return redisTemplate.boundValueOps(keyPrefix+key).get();
    }

    /**
     * 删除缓存
     * @param key 缓存的key
     */
    public void delete(String key){
        redisTemplate.delete(keyPrefix+key);
    }


}
