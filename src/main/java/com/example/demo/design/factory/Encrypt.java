package com.example.demo.design.factory;

/**
 * 加密
 *
 * @author dzm
 * @create 2018-03-20 18:03
 **/
public interface Encrypt {

    /**
     * 对密码进行加密
     * @param secret
     * @return
     */
    String encryptPwd(String secret,String secretSalt)throws Exception;

}
