package com.example.demo.design.facade;

/**
 * 模块B的实现类
 *
 * @author dzm
 * @create 2018-08-22 14:20
 **/
public class BModuleApiImpl implements BModuleApi{
    /**
     * 提供给外部系统
     */
    @Override
    public void b1() {
        System.out.println("模块B的b1方法");
    }

    @Override
    public void b2() {
        System.out.println("模块B的b2方法");
    }

    @Override
    public void b3() {
        System.out.println("模块B的b3方法");
    }
}
