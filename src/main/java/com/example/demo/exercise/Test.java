package com.example.demo.exercise;

import java.math.BigDecimal;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class Test {

    public static void main(String[] args) {
        BigDecimal a = new BigDecimal(633);
        BigDecimal b = new BigDecimal(100);
        BigDecimal c = a.divide(b,2,BigDecimal.ROUND_UP);
        System.out.println(c);
        System.out.println(c.multiply(new BigDecimal(100)));
        System.out.println(c.multiply(new BigDecimal(100)).setScale(0,BigDecimal.ROUND_UP));
    }


}
