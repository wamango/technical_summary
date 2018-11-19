package com.example.demo.design.decorator;

/**
 * 客户端-装饰器模式
 *
 * @author dzm
 * @create 2018-11-19 11:26
 **/
public class Client {
    public static void main(String[] args) {
//        Beverage beverage = new HouseBlend();
        Beverage beverage = new DarkRoast();
        beverage = new Mocha(beverage);
        beverage = new Milk(beverage);
        System.out.println(beverage.cost());
    }
}
