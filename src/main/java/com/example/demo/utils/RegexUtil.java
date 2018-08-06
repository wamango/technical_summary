package com.example.demo.utils;

import java.util.regex.Pattern;

/**
 * 正则工具类
 *
 * @author dzm
 * @create 2018-08-02 18:54
 **/
public class RegexUtil {

    /**
     * 校验是否满足正则表达式
     * @param testStr  被校验的字符串
     * @param regexStr 正则表达式
     * @return
     */
    public static boolean checkPattern(String testStr,String regexStr){
        return Pattern.matches(regexStr,testStr);
    }


}
