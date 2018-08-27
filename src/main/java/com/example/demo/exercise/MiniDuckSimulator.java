package com.example.demo.exercise;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class MiniDuckSimulator {

    public static void main(String[] args) {
        String regex = "^((13[0-9])|(14[5,7])|(15[0-3,5-9])|(17[0,3,5-8])|(18[0-9])|166|198|199|(147))\\d{8}$";
        Pattern p = Pattern.compile(regex, Pattern.CASE_INSENSITIVE);
        Matcher m = p.matcher("16663542365");
        System.out.println(m.matches());
    }

}
