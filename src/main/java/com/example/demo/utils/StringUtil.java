package com.example.demo.utils;


import java.lang.reflect.Field;

/**
 * 字符串工具类
 *
 * @author dzm
 * @create 2018-07-31 17:22
 **/
public class StringUtil {

    /**
     *  拼接类中属性的值
     * @param object
     * @param strings
     * @return
     */
    public  static String montageStr(Object object,String... strings) {
        Class clazz = object.getClass();
        Field[] fields = clazz.getDeclaredFields();
        StringBuilder stringBuilder = new StringBuilder();
        a:  for(Field field : fields){
            //true让我们在用反射时访问私有变量
            field.setAccessible(true);
            for(String str : strings){
                if(field.getName().equalsIgnoreCase(str)){
                    //跳出外层for循环的当前这次循环
                   continue a;
                }
            }
            Object obj = null;
            try {
                obj = field.get(object);
            } catch (IllegalAccessException e) {
                e.printStackTrace();
            }
            stringBuilder.append(obj==null?"":obj);
        }
        return stringBuilder.toString();
    }

}
