package com.example.demo.common;

/**
 * 正则常量类
 */
public interface RegexContants {

    /**校验中文*/
    String CHINESE_REGEX = "^[\\u4e00-\\u9fa5]{0,}$";

    /**密码(6-16位字母、数字)正则表达式*/
    String PASSWORD_REGEX ="^(?![0-9]+$)(?![a-zA-Z]+$)[0-9A-Za-z]{6,16}$";

    /**手机正则表达式*/
    String MOBLIE_REGEX = "^((13[0-9])|(14[5|7])|(15([0-3]|[5-9]))|(18[0,5-9]))\\d{8}$";

    /**固话表达式*/
    String TELEPHONE_REGEX = "^(0\\d{2}-\\d{8}(-\\d{1,4})?)|(0\\d{3}-\\d{7,8}(-\\d{1,4})?)$";

    /**邮箱正则表达式*/
    String EMAIL_REGEX = "^\\s*\\w+(?:\\.{0,1}[\\w-]+)*@[a-zA-Z0-9]+(?:[-.][a-zA-Z0-9]+)*\\.[a-zA-Z]+\\s*$";

    /**身份证正则表达式*/
    String ID_CARD_REGEX = "(^\\d{15}$)|(^\\d{18}$)|(^\\d{17}(\\d|X|x)$)";

    /**经度正则表达式*/
    String LONGITUDE_REGEX = "^-?(?:(?:180(?:\\.0{1,6})?)|(?:(?:(?:1[0-7]\\d)|(?:[1-9]?\\d))(?:\\.\\d{1,6})?))$";

    /**纬度正则表达式*/
    String LATITUDE_REGEX = "^-?(?:90(?:\\.0{1,6})?|(?:[1-8]?\\d(?:\\.\\d{1,6})?))$";

    /**金额正则表达式 正整数*/
    String MONEY_REGEX = "^[0-9]*[1-9][0-9]*$";


}
