package com.example.demo.design.factory;


import org.springframework.stereotype.Component;

/**
 * MD5
 *
 * @author dzm
 * @create 2018-03-20 19:15
 **/
@Component(value = "1")
public class MD5Encrypt implements Encrypt{


    /**
     * 对密码进行加密
     *
     * @param secret
     * @return
     */
    @Override
    public String encryptPwd(String secret,String secretSalt)throws Exception {
        return  "MD5";
    }
}
