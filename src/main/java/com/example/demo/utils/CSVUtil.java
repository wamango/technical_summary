package com.example.demo.utils;

import com.csvreader.CsvWriter;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

/**
 * 时间转换工具类
 *
 * @author dzm
 * @date 2018年7月31日
 */
public class CSVUtil {


    public static void writeCSV(){

        //获取文件夹名
        String dir = "C:/Users/dzm/Desktop/cp";

        //判断文件夹是否存在
        File dirFile = new File(dir);
        if (!dirFile.exists()) {
            dirFile.mkdirs();
        }
        File csvFile = new File("C:/Users/dzm/Desktop/cp/cp.csv");

        //判断文件是否存在
        if (!csvFile.exists()) {
            try {
                csvFile.createNewFile();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        Calendar calendar = Calendar.getInstance();
        FileWriter fileWriter = null;
        BufferedWriter bufferedWriter = null;
        CsvWriter csvWriter = null;

        try{
            fileWriter = new FileWriter(csvFile,true);
            bufferedWriter = new BufferedWriter(fileWriter);
            //创建CSV写对象
            csvWriter = new CsvWriter(bufferedWriter,',');

            //如果文件是第一次创建 写入列头
            List<String> list = new ArrayList<>();
            list.add("1");
            list.add("2654");
            csvWriter.writeRecord(list.toArray(new String[list.size()]));
            list = new ArrayList<>();
            list.add("2019091817515463439100");
            list.add("380998751340994561");
            //将List转String数组 写入文件中
            csvWriter.writeRecord(list.toArray(new String[list.size()]));
        } catch (IOException e) {
            e.printStackTrace();
        }finally {
            try{
                //关闭写
                bufferedWriter.close();
                fileWriter.close();
                csvWriter.close();
            } catch (IOException e){
                e.printStackTrace();
            }
        }

    }


}
