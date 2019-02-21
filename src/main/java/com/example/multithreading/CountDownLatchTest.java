package com.example.multithreading;

import java.util.concurrent.CountDownLatch;

/**
 * countDownLatch示例
 *
 * @author dzm
 * @create 2019-01-25 17:12
 **/
public class CountDownLatchTest {
    //创建一个countDownLatch实例
    private static CountDownLatch countDownLatch = new CountDownLatch(2);

//    public static void main(String[] args) throws InterruptedException{
//        ExecutorService executorService = Executors.newFixedThreadPool(2);
//        //将线程a添加到线程池
//        executorService.submit(new Runnable() {
//            @Override
//            public void run() {
//                try {
//                    TimeUnit.SECONDS.sleep(1);
//                } catch (InterruptedException e) {
//                    e.printStackTrace();
//                }finally {
//                    countDownLatch.countDown();
//                }
//                    System.out.println("childOne over");
//            }
//        });
//        //将线程b添加到线程池
//        executorService.submit(new Runnable() {
//            @Override
//            public void run() {
//                try {
//                    TimeUnit.SECONDS.sleep(1);
//                } catch (InterruptedException e) {
//                    e.printStackTrace();
//                }finally {
//                    countDownLatch.countDown();
//                }
//                System.out.println("childTwo over");
//            }
//        });
//        System.out.println("wait all child thread over");
//        //等待所有子线程返回
//        countDownLatch.await();
//        System.out.println("all child thread over");
//        executorService.shutdown();
//    }
}
