$(document).ajaxError(function (event, jXHR) {
    if (jXHR.status === 403 && jXHR.responseText === 'Unauthenticated') {
        var message = gettext(
            '현재 K-MOOC에서 로그아웃되신 상태입니다. '+
            '확인버튼을 클릭하시면 로그인페이지로 이동합니다. '+
            '취소버튼을 클릭하시면 현재 페이지에 머무릅니다. '+
            '(작업한 내역을 정확히 저장하시려면 반드시 로그인하세요)'
        );

        if (window.confirm(message)) {
            var currentLocation = window.location.href;
            window.location.href = '/login?next=' + currentLocation;
        };
    }
});
