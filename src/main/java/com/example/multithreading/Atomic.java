package com.example.multithreading;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 原子操作类
 *
 * @author dzm
 * @create 2019-01-30 14:25
 **/
public class Atomic {
    //创建Long型原子计数器
    private static AtomicLong atomicLong = new AtomicLong();
    //创建数据源
    private static Integer[] arrayOne = new Integer[]{0,1,2,3,0,5,6,0,56,0};
    private static Integer[] arrayTwo = new Integer[]{10,1,2,3,0,5,6,0,56,0};
    //创建一个countDownLatch实例
    private static CountDownLatch countDownLatch = new CountDownLatch(2);

//    public static void main(String[] args) throws InterruptedException{
//        //统计线程one的0的个数
//        Thread threadOne = new Thread(new Runnable() {
//            @Override
//            public void run() {
//                int size = arrayOne.length;
//                for (int i=0;i<size;++i){
//                    if(arrayOne[i].intValue()==0){
//                        //原子性设置原始值+1
//                        atomicLong.incrementAndGet();
//                    }
//                }
//            countDownLatch.countDown();
//            }
//        });
//
//        Thread threadTwo = new Thread(new Runnable() {
//            @Override
//            public void run() {
//                int size = arrayTwo.length;
//                for (int i=0;i<size;++i){
//                    if(arrayTwo[i].intValue()==0){
//                        //原子性设置原始值+1
//                        atomicLong.incrementAndGet();
//                    }
//                }
//                countDownLatch.countDown();
//            }
//        });
//        //启动线程
//        threadOne.start();
//        threadTwo.start();
//
//        //等待线程执行完毕
//        countDownLatch.await();
////        threadOne.join();
////        threadTwo.join();
//        System.out.println("count 0:"+atomicLong.get());
//    }
}
