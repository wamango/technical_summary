package com.example.demo.design.factory;


import org.springframework.stereotype.Component;

/**
 * ccks
 *
 * @author dzm
 * @create 2018-03-20 19:16
 **/
@Component(value = "2")
public class CCKSEncrypt implements Encrypt{


    /**
     * 对密码进行加密
     *
     * @param secret
     * @return
     */
    @Override
    public String encryptPwd(String secret,String secretSalt)throws Exception {
       return "CCKS";
    }


}
