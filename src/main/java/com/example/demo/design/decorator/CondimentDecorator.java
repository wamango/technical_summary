package com.example.demo.design.decorator;

/**
 * 调料-抽象装饰器
 *
 * @author dzm
 * @create 2018-11-19 11:19
 **/
public abstract class CondimentDecorator implements Beverage{
    protected Beverage beverage;
}
