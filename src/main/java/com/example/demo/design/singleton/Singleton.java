package com.example.demo.design.singleton;

/**
 * 单例
 *
 * @author dzm
 * @create 2018-11-15 9:57
 **/
public class Singleton {
    private Singleton(){

    }

//    private static Singleton  uniqueInstance;
//    /**
//     * 懒汉式-线程不安全
//     * 延迟加载，节约资源，但多线程情况下，会多个线程实例化
//     * @return
//     */
//    public static Singleton getUniqueInstance(){
//        if(uniqueInstance == null){
//            uniqueInstance = new Singleton();
//        }
//        return  uniqueInstance;
//    }

    /**
     * 懒汉式-线程安全
     * 性能不好，会堵塞线程
     * @return
     */
//    public static synchronized Singleton getUniqueInstance(){
//        if(uniqueInstance == null){
//            uniqueInstance = new Singleton();
//        }
//        return  uniqueInstance;
//    }




    /**
     * 饿汉式
     * 直接实例化不会造成多实例化，但是有可能浪费资源
     */
//    private static Singleton uniqueInstance = new Singleton();





//    /**
//     * uniqueInstace = new Singleton();这段代码是分为三步执行
//     *1.为 uniqueInstance 分配内存空间
//     *2.初始化 uniqueInstance
//     *3.将 uniqueInstance 指向分配的内存地址
//     *jvm具有指令重排序，执行顺序可能是1-3-2,重排序在多线程情况，可能导致uniqueInstance还未被初始化
//     *volatile可以禁止jvm指令重排序
//     */
//    private volatile static Singleton uniqueInstace;
//
//    /**
//     * 双重校验-线程安全
//     * @return
//     */
//    public static Singleton getUniqueInstace(){
//        if(uniqueInstace == null){
//            synchronized (Singleton.class){
//                //锁定没有实例化的对象
//                if(uniqueInstace == null){
//                    //防止两个线程同时进入
//                    uniqueInstace = new Singleton();
//                }
//            }
//        }
//        return uniqueInstace;
//    }


    /**
     * 静态内部类实现
     * 当Singleton类加载时，静态内部类SingletonHolder还没有被加载到内存里面
     * 只有当调用getUniqueInstace的时候触发SingletonHolder.INSTANCE时才会加载
     * 此时初始化INTANCE实例，并且jvm确保INSTANCE只被实例化一次
     * 好处：具有延迟加载初始化的好处，而且jvm提供了对线程安全的支持
     */
    private static class SingletonHolder{
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getUniqueInstace(){
        return SingletonHolder.INSTANCE;
    }
}
