package com.example.demo.design.factory.simpleFactory;

/**
 * 接口的具体实现类B
 *
 * @author dzm
 * @create 2019-02-13 16:44
 **/
public class ImplB implements Api {
    /**
     * 具体功能方法的定义
     *
     * @param s
     */
    @Override
    public void operation(String s) {
        //实现的功能具体实现
        System.out.println("implB s=="+s);
    }
}
