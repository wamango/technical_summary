package com.example.demo.design.decorator;

/**
 * 牛奶
 *
 * @author dzm
 * @create 2018-11-19 11:23
 **/
public class Milk extends CondimentDecorator {
    public Milk(Beverage beverage){
        this.beverage = beverage;
    }

    @Override
    public double cost() {
        return 1+beverage.cost();
    }
}
