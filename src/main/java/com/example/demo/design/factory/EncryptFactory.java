package com.example.demo.design.factory;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 加密工厂类
 *
 * @author dzm
 * @create 2018-03-20 20:05
 **/
@Component
public class EncryptFactory {
    private Map<String,Encrypt> map = new ConcurrentHashMap<>();
    @Autowired
    public EncryptFactory(Map<String,Encrypt> map){
        this.map = map;
    }

    public  String encryptPwdWay(int secretType,String secret,String secretSalt)throws Exception {
       String secretTypeStr = String.valueOf(secretType);
        return map.get(secretTypeStr).encryptPwd(secret,secretSalt);
    }
}
