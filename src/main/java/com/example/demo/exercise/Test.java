package com.example.demo.exercise;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class Test {
    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> {System.out.println("Hello World!");};
        Thread myThread = new Thread(task);
        myThread.start();
        myThread.join();

    }


}
