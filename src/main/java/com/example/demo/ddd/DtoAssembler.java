package com.example.demo.ddd;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

/**
* create by dengzhiming at 2021/5/19 9:25 上午
* description: 
* @return
* @param 
* @param 
* @param 
*/
@Mapper
public interface DtoAssembler {

    DtoAssembler INSTANCE = Mappers.getMapper(DtoAssembler.class);

    // 在这里只需要指出字段不一致的情况，支持复杂嵌套
    @Mapping(target = "userName", source = "user.phone")
    @Mapping(target = "type", source = "basic.roleType")
    UserDTO toDTO(User user, Basic basic);

    Basic toEntity(BasicDTO basicDTO);
}
