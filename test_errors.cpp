// 测试用例包含多种典型错误
class MissingSemicolon { /* 缺少分号错误 */ } 

int deleted_func() = delete;

void func(int x) {}
void func(const std::string& s) {}

template<typename T>
void template_func(T a) {}

int main() {
    // 错误1：缺少分号
    MissingSemicolon obj
    
    // 错误2：调用未定义函数
    undefined_function();
    
    // 错误3：函数调用不匹配
    func("hello");  // 需要static_cast<std::string>
    
    // 错误4：模板参数推导失败
    template_func("test");  // 需要明确模板类型
    
    // 错误5：使用已删除函数
    deleted_func();
    
    // 错误6：类型转换
    int* p = 123;  // 无效转换
    
    // 错误7：非void函数返回值问题
    if (false) {
        return 0;
    }
}