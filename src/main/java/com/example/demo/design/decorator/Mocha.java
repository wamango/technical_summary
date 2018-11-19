package com.example.demo.design.decorator;

/**
 * 摩卡咖啡
 *
 * @author dzm
 * @create 2018-11-19 11:23
 **/
public class Mocha extends CondimentDecorator {
    public Mocha(Beverage beverage){
        this.beverage = beverage;
    }

    @Override
    public double cost() {
        return 1+beverage.cost();
    }
}
