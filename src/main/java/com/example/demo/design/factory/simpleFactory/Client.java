package com.example.demo.design.factory.simpleFactory;

/**
 * 客户端
 *
 * @author dzm
 * @create 2019-02-13 16:49
 **/
public class Client {
    public static void main(String[] args) {
        Api api = Facory.createApi(1);
        api.operation("正在使用简单工厂类");
    }
}
