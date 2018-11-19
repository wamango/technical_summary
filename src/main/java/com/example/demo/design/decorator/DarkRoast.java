package com.example.demo.design.decorator;

/**
 * 焦糖咖啡
 *
 * @author dzm
 * @create 2018-11-19 11:10
 **/
public class DarkRoast  implements Beverage{

    @Override
    public double cost() {
        return 1;
    }
}
